#!/usr/bin/env python3
import click
import os

import pandas as pd
import numpy as np

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
    df = pd.read_csv(f"{os.environ['DBT_AREA_ROOT']}/sourcecode/tdemodules/config/mapping.txt", delim_whitespace = True, names = ["Crate", "AMC", "AMC_channel", "CRP", "view_type", "view_channel"])
    if det_name == "tde-testcrate":
        df = df[df["Crate"] == 0]
        df = df[np.any([df["AMC"] == i for i in [1, 6, 7]], 0)]
        # there may be less channels in the testcrate, but for now this is fine.

    df["CRP"] += base_sid # This is needed to assign the source ID correctly for the TDE ()
    return df


def get_mapping_from_channel_map(channel_map : str):
    df = pd.read_csv(channel_map, sep=r'\s+', names = ['offlchan', 'detid', 'detelement', 'crate', 'slot', 'stream', 'streamchan', 'plane', 'chan_in_plane', 'femb', 'asic ', 'asicchan'])

    df23 = df[df['detelement'] < 4]

    df_map = df23[['crate','slot', 'streamchan', 'detelement', 'plane', 'chan_in_plane']]
    df_map.columns = ["Crate", "AMC", "AMC_channel", "CRP", "view_type", "view_channel"]
    return df_map


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

@click.command
@click.option("--det_name", "-d", type = click.Choice(["tde", "tde-testcrate"]), default = "tde", help = "Detector element readout.")
@click.option("--source_id", "-s", type = int, default = 2, help = "Base source ID number.")
@click.option("--det_id", "-D", type = int, default = 11, help = "Detector id.")
@click.option("--sid_suffix", is_flag = "store_true", help = "Use source ID as the suffix for the AMCDetDataSenders.")
@click.option("channel_map", "-c", type = str, default = None, help = "ProtoDUNE channel map to infer the Crate/AMC mapping.")
def main(det_name, source_id, det_id, sid_suffix, channel_map):
    # key is crate number, so 10.73.(n+32).128, value is the number of AMCs each crate has installed.

    if channel_map:
        mapping = get_mapping_from_channel_map(channel_map)
    else:
        mapping = get_mapping(det_id, source_id)
    print(mapping)

    db = create_db(f"crp23-det-senders", get_includes())

    sid_counters = {i : i * 100 for i in pd.unique(mapping["CRP"])}
    for cg in [[0, 1, 2, 6, 7], [3, 4, 5, 8, 9]]:
        streams = []
        # resource = db.create_obj("NetworkDetectorToDaqConnection", f"{det_name}-senders-crate-{'-'.join([str(c) for c in cg])}")
        for crate in cg:
            crate_map = mapping[mapping["Crate"] == crate]
            amcs = pd.unique(crate_map["AMC"])
            for amc in amcs:
                name = f"crate{crate}-slot{amc}"
                base_sid = pd.unique(crate_map[crate_map["AMC"] == amc]["CRP"])[0]
                sid_counters[base_sid] += 1

                amc_net_info = calculate_amc_net_info(crate, amc)
                geo = db.create_obj(class_name = "GeoId", uid = f"geoId-{det_name}-amc-{sid_counters[base_sid]}")
                geo["detector_id"] = det_id # channel map may be required for this ()
                geo["crate_id"] = crate
                geo["slot_id"] = amc

                ds = db.create_obj(class_name = "DetectorStream", uid = f"DetStream-{sid_counters[base_sid]}")
                ds["source_id"] = sid_counters[base_sid]
                ds["geo_id"] = geo

                nw_send = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{det_name}-amc-{name}-10g")
                nw_send["mac_address"] = amc_net_info["mac_10g"]
                nw_send["ip_address"] = [amc_net_info["ip_10g"]]
                nw_send["network_name"] = "Data"
                
                nw_rec = db.create_obj(class_name = "NetworkInterface", uid = f"nw-{det_name}-amc-{name}-1g")
                nw_rec["mac_address"] = amc_net_info["mac_1g"]
                nw_rec["ip_address"] = [amc_net_info["ip_1g"]]
                nw_rec["network_name"] = "Control"

                sender_names = sid_counters[base_sid] if sid_suffix else name
                dds = db.create_obj(class_name = "TdeAmcDetDataSender", uid = f"dds-{det_name}-amc-{sender_names}")
                dds["port"] = 54321 + amc + 1
                dds["control_host"] = f"np02-amc-{sid_counters[base_sid]}" # This should be the source ID
                dds["uses"] = nw_send
                dds["control_endpoint"] = nw_rec
                dds["streams"] = [ds]
                streams.append(dds)
        # resource["net_senders"] = streams
    db.commit()
    return


if __name__ == "__main__":
    main()