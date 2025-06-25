#!/usr/bin/env python3
import argparse

import pandas as pd
import numpy as np
import pathlib

from daqconf.utils import find_oksincludes
import conffwk

from rich import print


def get_includes(db_path : str) -> list[str]:
    include_files = [
        "schema/confmodel/dunedaq.schema.xml",
        "schema/appmodel/application.schema.xml",
        "schema/appmodel/fdmodules.schema.xml",
        "schema/appmodel/tde.schema.xml",
    ]
    res, extra_includes = find_oksincludes(["hw/hosts.data.xml", "defaults/ccm.data.xml"], [db_path])
    if res:
        include_files += extra_includes
    print(include_files)
    return include_files


def get_mapping(det_name : str, base_sid : int) -> pd.DataFrame:
    fp = pathlib.Path(__file__).parents[1].resolve()
    df = pd.read_csv(f"{fp}/config/mapping.txt", delim_whitespace = True, names = ["Crate", "AMC", "AMC_channel", "CRP", "view_type", "view_channel"])
    if det_name == "tde-testcrate":
        df = df[df["Crate"] == 0]
        df = df[np.any([df["AMC"] == i for i in [1, 6, 7]], 0)]
        # there may be less channels in the testcrate, but for now this is fine.

    df["CRP"] += base_sid # This is needed to assign the source ID correctly for the TDE ()
    return df


def create_db(oksfile : str, include_files : list[str]) -> conffwk.Configuration:
    db = conffwk.Configuration("oksconflibs")
    if not oksfile.endswith(".data.xml"):
        oksfile = oksfile + ".data.xml"
    print(f"Creating OKS database file {oksfile}")
    db.create_db(oksfile, include_files)
    db.set_active(oksfile)
    return db


def calculate_amc_net_info(crate, slot):
    return {
        "ip_1g" : f"10.73.{crate + 32}.{slot + 1}",
        "ip_10g" : f"10.73.{crate + 32}.{slot + 13}",
        "mac_1g" : "00:07:ED:A1:%02x:%02x" % (crate + 1, slot + 1),
        "mac_10g" : "00:07:ED:A2:%02x:%02x" % (crate + 1, slot + 13),
    }


def create_det_connections(args : argparse.Namespace):
    # key is crate number, so 10.73.(n+32).128, value is the number of AMCs each crate has installed.
    mapping = get_mapping(args.det_name, args.sid)

    for crp in pd.unique(mapping["CRP"]):
        amc_map = {}
        crp_map = mapping[mapping["CRP"] == crp]
        for crate in pd.unique(crp_map["Crate"]):
            amc_map[crate] = pd.unique(crp_map[crp_map["Crate"] == crate]["AMC"])

        db = create_db(f"crp{crp}-det-connections", get_includes(args.db_path))

        d2d = db.create_obj("DetectorToDaqConnection", f"{args.det_name}-connections")

        # create the AMC related objects
        con = []
        resources = {c : db.create_obj("ResourceSetAND", f"{args.det_name}-senders-crp{crp}-crate{c}") for c in amc_map}

        base_sid = 100 * crp
        for n, amcs in amc_map.items():
            resource = resources[n]
            ddss = []
            for m in amcs:
                base_sid += 1
                
                amc_net_info = calculate_amc_net_info(n, m)
                geo = db.create_obj(class_name = "GeoId", uid = f"geoId-{args.det_name}-amc-{base_sid}")
                geo["detector_id"] = args.det_id # channel map may be required for this ()
                geo["slot_id"] = m

                ds = db.create_obj(class_name = "DetectorStream", uid = f"DetStream-{base_sid}")
                ds["source_id"] = base_sid
                ds["geo_id"] = geo

                nw_send = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-10g")
                nw_send["mac_address"] = amc_net_info["mac_10g"]
                nw_send["ip_address"] = [amc_net_info["ip_10g"]]
                nw_send["network_name"] = "Data"
                
                nw_rec = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{base_sid}-1g")
                nw_rec["mac_address"] = amc_net_info["mac_1g"]
                nw_rec["ip_address"] = [amc_net_info["ip_1g"]]
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

        # TDEAMCModuleConf (completely a dummy object, as AMCs cannot be configured at the moment) 
        mod_conf = db.create_obj("TDEAMCModuleConf", "amc_module_conf")

        # make the TDECrateApp
        app = db.create_obj(class_name = "TDECrateApplication", uid = f"crp{crp}-crate-application")
        app["application_name"] = "daq_application"
        app["runs_on"] = db.get_obj(class_name = "VirtualHost", uid = f"vh-{args.control_host}") # will the virtual host for control change?
        app["exposes_service"] = [db.get_obj(class_name = "Service", uid = "daqapp_control")]
        app["opmon_conf"] = db.get_obj(class_name = "OpMonConf", uid = "slow-all-monitoring")

        app["contains"] = [d2d]
        app["tde_amc_module_conf"] = mod_conf

        db.commit()
    return



if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate configuration objects for TDE readout.")

    parser.add_argument(dest = "db_path", type = str, help = "path to oks database.")
    parser.add_argument("-f", "--frontend", dest = "det_name", type = str, choices = ["tde", "tde-testcrate"], default = "tde-testcrate", help = "frontend components to readout.")
    parser.add_argument("-s", "--source-id", dest = "sid", type = int, default = 2, help = "base source ID number.")
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
