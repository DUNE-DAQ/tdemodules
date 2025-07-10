#!/usr/bin/env python3
import argparse

import pandas as pd
import numpy as np
import pathlib

import conffwk

from rich import print


def get_includes() -> list[str]:
    include_files = [
        "schema/confmodel/dunedaq.schema.xml",
        "schema/appmodel/application.schema.xml",
        "schema/appmodel/fdmodules.schema.xml",
        "schema/appmodel/tde.schema.xml",
    ]
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

    db = create_db(f"crp23-det-senders", get_includes())


    sid_counters = {i : i * 100 for i in pd.unique(mapping["CRP"])}
    for cg in [range(0, 5), range(5, 10)]:
        streams = []
        resource = db.create_obj("ResourceSetAND", f"{args.det_name}-senders-crate-{min(cg)}-{max(cg)}")
        for crate in cg:
            crate_map = mapping[mapping["Crate"] == crate]
            amcs = pd.unique(crate_map["AMC"])
            for amc in amcs:
                name = f"crate{crate}-slot{amc}"
                base_sid = pd.unique(crate_map[crate_map["AMC"] == amc]["CRP"])[0]
                sid_counters[base_sid] += 1
                sid_counters[base_sid]

                amc_net_info = calculate_amc_net_info(crate, amc)
                geo = db.create_obj(class_name = "GeoId", uid = f"geoId-{args.det_name}-amc-{sid_counters[base_sid]}")
                geo["detector_id"] = args.det_id # channel map may be required for this ()
                geo["slot_id"] = amc

                ds = db.create_obj(class_name = "DetectorStream", uid = f"DetStream-{sid_counters[base_sid]}")
                ds["source_id"] = sid_counters[base_sid]
                ds["geo_id"] = geo

                nw_send = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{name}-10g")
                nw_send["mac_address"] = amc_net_info["mac_10g"]
                nw_send["ip_address"] = [amc_net_info["ip_10g"]]
                nw_send["network_name"] = "Data"
                
                nw_rec = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{args.det_name}-amc-{name}-1g")
                nw_rec["mac_address"] = amc_net_info["mac_1g"]
                nw_rec["ip_address"] = [amc_net_info["ip_1g"]]
                nw_rec["network_name"] = "Control"

                sender_names = sid_counters[base_sid] if args.sid_suffix else name
                dds = db.create_obj(class_name = "TdeAmcDetDataSender", uid = f"dds-{args.det_name}-amc-{sender_names}")
                dds["port"] = 54321 + amc + 1
                dds["control_host"] = f"np02-amc-{sid_counters[base_sid]}" # This should be the source ID
                dds["contains"] = [ds] # This should be the DetStream object
                dds["uses"] = nw_send
                dds["control_endpoint"] = nw_rec
                streams.append(dds)
        resource["contains"] = streams
    db.commit()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate configuration objects for TDE readout.")

    parser.add_argument("-f", "--frontend", dest = "det_name", type = str, choices = ["tde", "tde-testcrate"], default = "tde-testcrate", help = "frontend components to readout.")
    parser.add_argument("-s", "--source-id", dest = "sid", type = int, default = 2, help = "base source ID number.")
    parser.add_argument("-D", "--det_id", dest = "det_id", type = int, default = 11, help = "detector id.")
    parser.add_argument("--sid_suffix", dest = "sid_suffix", action = "store_true", help = "use source ID as the suffix for the AMCDetDataSenders.")

    args = parser.parse_args()
    print(args)

    create_det_connections(args)
