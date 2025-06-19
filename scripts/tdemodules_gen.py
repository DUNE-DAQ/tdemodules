#!/usr/bin/env python3
import argparse

import pandas as pd
import numpy as np
import pathlib

from daqconf.utils import find_oksincludes
import conffwk

import get_mac

from rich import print

#* Try to make segments without closing the det-connections file (can you have both open?) then commit together

#* MAC addresses:
##* 10g AMC network; are these needed in the config
##* 1g AMC network; are these needed in the config? (doesn't look like it?)
##* How to get MAC addresses (cant ping AMCs directly and use arp)

#* add instructions on what to complete by hand e.g. NIC devices, user needs to add the IPs/PCIes and MACs thenselves

def get_mapping(det_name : str, base_sid : int) -> pd.DataFrame:
    fp = pathlib.Path(__file__).parents[1].resolve()
    df = pd.read_csv(f"{fp}/config/mapping.txt", delim_whitespace = True, names = ["Crate", "AMC", "AMC_channel", "CRP", "view_type", "view_channel"])
    if det_name == "tde-testcrate":
        df = df[df["Crate"] == 0]
        df = df[np.any([df["AMC"] == i for i in [1, 6, 7]], 0)]
        # there may be less channels in the testcrate, but for now this is fine.

    df["CRP"] += base_sid # This is needed to assign the source ID correctly for the TDE ()
    return df


def get_includes() -> list[str]:
    include_files = [
        "schema/confmodel/dunedaq.schema.xml",
        "schema/appmodel/application.schema.xml",
        "schema/appmodel/fdmodules.schema.xml",
        "schema/appmodel/tde.schema.xml",
    ]
    res, extra_includes = find_oksincludes(["hw/hosts.data.xml", "defaults/ccm.data.xml", "defaults/connections.data.xml", "defaults/data-store-params.data.xml", "defaults/fsm.data.xml", "defaults/moduleconfs.data.xml", "defaults/wiecconfs.data.xml"], ["/nfs/home/sbhuller/fddaq-v5.3.2-rc2-a9/runarea/ehn1-daqconfigs/"])
    if res:
        include_files += extra_includes
    print(include_files)
    return include_files


def create_db(oksfile : str, include_files : list[str]) -> conffwk.Configuration:
    db = conffwk.Configuration("oksconflibs")
    if not oksfile.endswith(".data.xml"):
        oksfile = oksfile + ".data.xml"
    print(f"Creating OKS database file {oksfile}")
    db.create_db(oksfile, include_files)
    db.set_active(oksfile)
    return db


def create_det_connections(args : argparse.Namespace):
    dpdk_host = args.dpdk_host.replace("-", "")

    # key is crate number, so 10.73.(n+32).128, value is the number of AMCs each crate has installed.
    mapping = get_mapping(args.det_name, args.sid)
    print(mapping)

    structured_maps = {}
    for crp in pd.unique(mapping["CRP"]):
        amc_map = {}
        crp_map = mapping[mapping["CRP"] == crp]
        for crate in pd.unique(crp_map["Crate"]):
            amc_map[crate] = pd.unique(crp_map[crp_map["Crate"] == crate]["AMC"])
        structured_maps[crp] = amc_map

    db = create_db("tde-det-connections", get_includes())

    d2d = db.create_obj("DetectorToDaqConnection", f"{args.det_name}-connections")

    # create the DPDKRecievers, DPDKPortConfigs, Processing Resource
    dpdk_receivers = []

    for i in range(len(structured_maps)): # one 100G NIC for one CRP
        nw_device = db.create_obj("NetworkDevice", f"nic-{dpdk_host}-numa{i}")
        lcores = db.create_obj("ProcessingResource", f"lcores-{dpdk_host}-numa{i}")

        dpdk_port_conf = db.create_obj("DPDKPortConfiguration", f"dpdk-{dpdk_host}-numa{i}-conf")
        dpdk_port_conf["used_lcores"] = [lcores]

        dpdk_receiver = db.create_obj("DPDKReceiver", f"dpdk-{dpdk_host}-receiver{i}")
        dpdk_receiver["uses"] = nw_device
        dpdk_receiver["configuration"] = dpdk_port_conf
        dpdk_receivers.append(dpdk_receiver)

    # create the AMC related objects
    con = []
    resources = {c : db.create_obj("ResourceSetAND", f"{args.det_name}-senders-crate{c}") for c in pd.unique(mapping["Crate"])}

    for s, amc_map in structured_maps.items():
        base_sid = 100 * s
        for n, amcs in amc_map.items():
            resource = resources[n]
            ddss = []
            for m in amcs:
                base_sid += 1
                geo = db.create_obj(class_name = "GeoId", uid = f"geoId-{args.det_name}-amc-{base_sid}")
                geo["detector_id"] = args.det_id # channel map may be required for this ()
                geo["slot_id"] = m

                ds = db.create_obj(class_name = "DetectorStream", uid = f"DetStream-{base_sid}")
                ds["source_id"] = base_sid
                ds["geo_id"] = geo

                nw_send = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-10g")
                # nw_send["mac_address"] need to do this at some point
                nw_send["ip_address"] = [f"10.73.{n + 32}.{m + 13}"]
                nw_send["network_name"] = "Data"
                
                nw_rec = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-1g")
                ip = f"10.73.{n + 32}.{m + 1}"
                nw_rec["ip_address"] = [ip]
                nw_rec["mac_address"] = get_mac.get_mac(args.control_host, ip)
                nw_rec["network_name"] = "Control"

                dds = db.create_obj(class_name = "TdeAmcDetDataSender", uid = f"dds-{args.det_name}-amc-{base_sid}")
                dds["port"] = 54321 + m + 1
                dds["control_host"] = f"np02-amc-{base_sid}" # This should be the source ID
                dds["contains"] = [ds] # This should be the DetStream object
                dds["uses"] = nw_send
                dds["control_endpoint"] = nw_rec
                ddss.append(dds)

            resource["contains"] = ddss
            con.append(resource)

    d2d["contains"] = con + dpdk_receivers

    # TDEAMCModuleConf (completely a dummy object, as AMCs cannot be configured at the moment) 
    mod_conf = db.create_obj("TDEAMCModuleConf", "amc_module_conf")

    # make the TDECrateApp
    app = db.create_obj(class_name = "TDECrateApplication", uid = f"{args.det_name}-crate-application")
    app["application_name"] = "daq_application"
    app["runs_on"] = db.get_obj(class_name = "VirtualHost", uid = f"vh-{args.control_host}") # will the virtual host for control change?
    app["exposes_service"] = [db.get_obj(class_name = "Service", uid = "daqapp_control")]
    app["opmon_conf"] = db.get_obj(class_name = "OpMonConf", uid = "slow-all-monitoring")

    app["contains"] = [d2d]
    app["tde_amc_module_conf"] = mod_conf

    db.commit()
    return


def create_segment(args : argparse.Namespace):
    dpdk_host = args.dpdk_host.replace("-", "")

    mapping = get_mapping(args.det_name, args.sid)
    crp_nums = pd.unique(mapping["CRP"])

    include_files = get_includes()
    include_files.append("tde-det-connections.data.xml")
    db = create_db(args.det_name, include_files)

    # Services
    rest = db.create_obj("Service", "dynamic_rest_control")
    rest["protocol"] = "rest"
    rest["port"] = 0
    grpc = db.create_obj("Service", "dynamic_grpc_control")
    grpc["protocol"] = "grpc"
    grpc["port"] = 0
    db.create_obj("Service", f"{args.det_name}_timesync") #? timesync not assigned anywhere, is this needed?

    # TPSourceConf
    #! make in threes (3 for the testcrate and 6 for the tde)
    tp_sids = []
    for c in crp_nums:
        for i in range(3):
            sid = (c * 10) + i
            conf = db.create_obj("SourceIDConf", f"tp-srcid-{sid}")
            conf["sid"] = sid
            conf["subsystem"] = "Trigger"
            tp_sids.append(conf)

    # RoHwConfig
    rohw = db.create_obj("RoHwConfig", f"{dpdk_host}-numa0-hw-cfg") # Only one is needed for the NP02ReadoutApplication

    # AVXThresholdProcessor
    avx = db.create_obj("AVXThresholdProcessor", f"tpg-threshold-proc-{args.det_name}")

    # RawDataProcessor
    proc = db.create_obj("RawDataProcessor", f"def-tde-processor-{args.det_name}")
    proc["queue_sizes"] = 50000
    proc["thread_names_prefix"] = "rawproc-"
    proc["latency_monitoring"] = 1
    proc["channel_map"] = args.channel_map
    proc["processing_steps"] = [
        db.get_obj("AVXFrugalPedestalSubtractProcessor", "tpg-pedsub-proc"),
        avx
    ]
    proc["sot_minima"] = db.get_obj("SamplesOverThresholdMinima", "def-sot-minima")

    # DataHandlerConf
    reqhandler = db.get_obj(class_name="RequestHandler", uid="def-data-request-handler")
    latencybuffer = db.get_obj(class_name="LatencyBuffer", uid=f"tpc-latency-buf-numa0") # we hack the LB numa assignment, so just use the default numa0 config 

    data_handler = db.create_obj("DataHandlerConf", f"def-tpc-link-handler-{args.det_name}")
    data_handler["template_for"] = "FDDataHandlerModule"
    data_handler["input_data_type"] = "TDEEthFrame"
    data_handler["generate_timesync"] = True
    data_handler["request_handler"] = reqhandler
    data_handler["latency_buffer"] = latencybuffer
    data_handler["data_processor"] = proc


    # ReadoutApplication
    opmon_conf = db.get_obj("OpMonConf", "slow-all-monitoring")
    ru_app = db.create_obj("NP02ReadoutApplication", f"ru{dpdk_host}eth")
    ru_app["application_name"] = "daq_application"
    ru_app["tp_generation_enabled"] = True
    ru_app["ta_generation_enabled"] = False
    ru_app["contains"] = [db.get_obj("DetectorToDaqConnection", f"{args.det_name}-connections")]
    ru_app["runs_on"] = db.get_obj("VirtualHost", "vh-np02-srv-002")
    ru_app["exposes_service"] = [rest]
    ru_app["opmon_conf"] = opmon_conf

    queue_rules = ["fd-dlh-data-requests-queue-rule", "fa-queue-rule", "tp-queue-rule", "tde-callback-raw-data-rule"]
    ru_app["queue_rules"] = [db.get_obj("QueueConnectionRule", i) for i in queue_rules]

    net_rules = ["ta-net-rule", "tpset-net-rule", "ts-net-rule", "data-req-readout-net-rule"]
    ru_app["network_rules"] = [db.get_obj("NetworkConnectionRule", i) for i in net_rules]

    ru_app["action_plans"] = [db.get_obj("ActionPlan", i) for i in ["readout-start", "readout-stop"]]

    ru_app["tp_source_ids"] = tp_sids
    ru_app["uses"] = rohw
    ru_app["link_handler"] = data_handler
    ru_app["tp_handler"] = db.get_obj("DataHandlerConf", "def-tpc-tp-handler-numa0")
    ru_app["data_reader"] = db.get_obj("DPDKReaderConf", "def-nic-receiver-conf")

    # RCApplication
    rc_app = db.create_obj("RCApplication", "tde-testcrate-controller")
    rc_app["application_name"] = "drunc-controller"
    rc_app["runs_on"] = db.get_obj("VirtualHost", "vh-np04-srv-024")
    rc_app["exposes_service"] = [grpc]
    rc_app["opmon_conf"] = opmon_conf
    rc_app["fsm"] = db.get_obj("FSMconfiguration", "FSMconfiguration_noAction")
    rc_app["broadcaster"] = db.get_obj("RCBroadcaster", "broadcaster-root")

    # Segment
    segment = db.create_obj("Segment", f"{args.det_name}-segment")    
    segment["applications"] = [ru_app, db.get_obj("TDECrateApplication", f"{args.det_name}-crate-application")]
    segment["controller"] = rc_app

    db.commit()
    return


def create_session(args):
    include_files = get_includes()

    res, extra_includes = find_oksincludes(["segments/dataflow.data.xml", "segments/trigger.data.xml", "segments/hsi.data.xml"], ["/nfs/home/sbhuller/fddaq-v5.3.2-rc2-a9/runarea/ehn1-daqconfigs/"])

    if res:
        include_files += extra_includes

    include_files += ["tde-det-connections.data.xml", f"{args.det_name}.data.xml"]
    db = create_db(f"{args.det_name}-session", include_files)

    # DetectorConfig
    det_conf = db.create_obj("DetectorConfig", "np02-detector")
    det_conf["tpg_channel_map"] = args.channel_map
    det_conf["clock_speed_hz"] = 62500000
    det_conf["op_env"] = "np02vd"
    det_conf["offline_data_stream"] = "cosmics"

    # Segment
    segment = db.create_obj("Segment", "root-segment")
    segment["segments"] = [
        db.get_obj("Segment", f"{args.det_name}-segment"),
        db.get_obj("Segment", "df-segment"),
        db.get_obj("Segment", "trg-segment"),
    ]
    segment["controller"] = db.get_obj("RCApplication", "root-controller")


    # Session
    session = db.create_obj("Session", "tde-testcrate-session")
    session["data_request_timeout_ms"] = 1000
    session["data_rate_slowdown_factor"] = 1
    session["controller_log_level"] = "INFO"
    session["log_path"] = "/log"
    session["connectivity_service"] = db.get_obj("ConnectivityService", "ehn1-connectivity-service-config")
    session["environment"] = [db.get_obj("VariableSet", "ehn1-variables")]
    session["disabled"]  = [
        # how to do this...
        db.get_obj("DFApplication", "df-s01-d2"),
        db.get_obj("DFApplication", "df-s01-d3"),
        db.get_obj("DFApplication", "df-s02-d0"),
        db.get_obj("DFApplication", "df-s02-d1"),
        db.get_obj("DFApplication", "df-s02-d2"),
        db.get_obj("DFApplication", "df-s02-d3"),
        db.get_obj("DFApplication", "df-s03-d0"),
        db.get_obj("DFApplication", "df-s03-d1"),
        db.get_obj("DFApplication", "df-s03-d2"),
        db.get_obj("DFApplication", "df-s03-d3"),
        db.get_obj("DFApplication", "df-s04-d1"),
        db.get_obj("DFApplication", "df-s04-d2"),
        db.get_obj("DFApplication", "df-s04-d3"),
        db.get_obj("DFApplication", "df-s05-d0"),
        db.get_obj("DFApplication", "df-s05-d1"),
        db.get_obj("DFApplication", "df-s05-d2"),
        db.get_obj("DFApplication", "df-s05-d3"),
        db.get_obj("DFApplication", "df-s05-d4"),
        db.get_obj("DFApplication", "df-s05-d5"),
        db.get_obj("DFApplication", "df-s04-d0")
    ]
    session["segment"] = segment
    session["detector_configuration"] = det_conf
    session["opmon_uri"] = db.get_obj("OpMonURI", "cern-opmon-uri")

    db.commit()
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate configuration objects for TDE readout.")

    parser.add_argument("-f", "--frontend", dest = "det_name", type = str, choices = ["tde", "tde-testcrate"], default = "tde-testcrate", help = "frontend components to readout.")
    parser.add_argument("-d", "--dpdk-host", dest = "dpdk_host", type = str, default = "np02-srv-002", help = "readout application host")
    parser.add_argument("-s", "--source-id", dest = "sid", type = int, default = 8, help = "base source ID number.")
    parser.add_argument("-D", "--det_id", dest = "det_id", type = int, default = 11, help = "detector id.")
    parser.add_argument("-C", "--control-host", dest = "control_host", type = str, default = "np04-srv-011", help = "Control host machine for AMCs")


    available_cmaps = [
        "FiftyLTPCChannelMap",
        "ICEBERGChannelMap",
        "HDColdboxTPCChannelMap",
        "PD2HDTPCChannelMap",
        "VDColdboxTPCChannelMap",
        "PD2VDBottomTPCChannelMap",
        "PD2VDTPCChannelMap",
        "DummyTPCChannelMap",
    ]
    parser.add_argument("-c", "--channel-map", dest = "channel_map", type = str, choices = available_cmaps, default = "PD2VDTPCChannelMap")

    args = parser.parse_args()
    print(args)

    create_det_connections(args)
    create_segment(args)
    create_session(args)