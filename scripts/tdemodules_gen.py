#!/usr/bin/env python3
import argparse

from daqconf.utils import find_oksincludes
import conffwk

from rich import print

def create_det_connections(args : argparse.Namespace):
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

    dpdk_host = args.dpdk_host.replace("-", "")

    # key is crate number, so 10.73.(n+32).128, value is the number of AMCs each crate has installed.
    crate_map = {
        0 : range(10),
        1 : range(10),
        2 : range(10),
        3 : range(10),
        4 : range(10),
        5 : range(10),
        6 : range(10),
        7 : range(8),
        8 : range(8),
        9 : range(10)
    } #? use the mapping.txt files instead?

    crate_map = {0 : [1, 6, 7]} # tde test crate

    oksfile = "tde-det-connections"

    dal = conffwk.dal.module("generated", include_files)
    db = conffwk.Configuration("oksconflibs")
    if not oksfile.endswith(".data.xml"):
        oksfile = oksfile + ".data.xml"
    print(f"Creating OKS database file {oksfile}")
    db.create_db(oksfile, include_files)
    db.set_active(oksfile)

    # for 10g data senders, the ip is 10.73.(n+32).(m+13), m is the slot number of the AMC (0-9)
    # for 1g data control, the ip is 10.73.(n+32).(m+1)
    d2d = db.create_obj("DetectorToDaqConnection", f"{args.det_name}-connections")


    # create the DPDKRecievers, DPDKPortConfigs, Processing Resource
    nw_device = db.create_obj("NetworkDevice", f"nic-{dpdk_host}-numa{args.numa}")
    lcores = db.create_obj("ProcessingResource", f"lcores-{dpdk_host}-numa{args.numa}")

    dpdk_port_conf = db.create_obj("DPDKPortConfiguration", f"dpdk-{dpdk_host}-numa{args.numa}-conf")
    dpdk_port_conf["used_lcores"] = [lcores]

    dpdk_receiver = db.create_obj("DPDKReceiver", f"dpdk-{dpdk_host}-receiver")
    dpdk_receiver["uses"] = nw_device
    dpdk_receiver["configuration"] = dpdk_port_conf

    # create the AMC related objects
    con = []
    base_sid = args.sid
    for n, amcs in crate_map.items():
        resource = db.create_obj("ResourceSetAND", f"{args.det_name}-senders-crate{n}")
        ddss = []
        for m in amcs:
            base_sid += 1
            geo = db.create_obj(class_name = "GeoId", uid = f"geoId-{args.det_name}-amc-{base_sid}")
            geo["detector_id"] = n # what is this for tde? just the crate number?
            geo["slot_id"] = m

            ds = db.create_obj(class_name = "DetectorStream", uid = f"DetStream-{base_sid}")
            ds["source_id"] = base_sid
            ds["geo_id"] = geo

            nw_send = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-10g")
            #nw_send["mac_address"] need to do this at some point
            nw_send["ip_address"] = [f"10.73.{n + 32}.{m + 13}"]
            nw_send["network_name"] = "Data"
            
            nw_rec = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-1g")
            #nw_send["mac_address"] need to do this at some point
            nw_rec["ip_address"] = [f"10.73.{n + 32}.{m + 1}"]
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

    d2d["contains"] = con

    # make the TDECrateApp
    app = db.create_obj(class_name = "TDECrateApplication", uid = f"{args.det_name}-crate-application")
    app["application_name"] = "daq_application"
    app["runs_on"] = db.get_obj(class_name = "VirtualHost", uid = "vh-np04-srv-011") # will the virtual host for control change?
    app["exposes_service"] = [db.get_obj(class_name = "Service", uid = "daqapp_control")]
    app["opmon_conf"] = db.get_obj(class_name = "OpMonConf", uid = "slow-all-monitoring")

    app["contains"] = [d2d]
    db.commit()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate configuration objects for TDE readout.")

    parser.add_argument("-f", "--frontend", dest = "det_name", type = str, choices = ["tde", "tde-testcrate"], default = "tde-testcrate", help = "frontend components to readout.")
    parser.add_argument("-d", "--dpdk-host", dest = "dpdk_host", type = str, default = "np02-srv-002", help = "readout application host")
    parser.add_argument("-n", "--numa", dest = "numa", type = int, default = 0, help = "NUMA region for NIC")
    parser.add_argument("-s", "--source-id", dest = "sid", type = int, default = 900, help = "base source ID number.")

    args = parser.parse_args()
    print(args)

    create_det_connections(args)