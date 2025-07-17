#!/usr/bin/env python3
import click

import json

import pandas as pd

from rich import print

from tde_stream_db_gen import get_mapping_from_channel_map


@click.command
@click.option("-c", "--channel_map", type = str, help = "ProtoDUNE channel map to infer the Crate/AMC mapping.")
def main(channel_map):
    mapping = get_mapping_from_channel_map(channel_map)

    thread_name_prefix_ru = [
        "rawproc-0",
        "cleanup",
        "consumer",
        "recording",
        "periodic"
    ]
    thread_name_prefix_tpg = [
        "tpproc-0",
        "cleanup",
        "consumer",
        "periodic"
    ]

    crate_group = [[0, 1, 2, 6, 7], [3, 4, 5, 8, 9]]

    sids = {i : [] for i in range(len(crate_group))}
    sid_counters = {i : i * 100 for i in pd.unique(mapping["CRP"])}

    for cg in crate_group:
        for crate in cg:
            crate_map = mapping[mapping["Crate"] == crate]
            amcs = pd.unique(crate_map["AMC"])
            for amc in amcs:
                base_sid = pd.unique(crate_map[crate_map["AMC"] == amc]["CRP"])[0]
                sid_counters[base_sid] += 1

                index = [crate in i for i in crate_group][0]
                sids[index].append(str(sid_counters[base_sid]))

    template = {"thread_group" : []}
    for (n, v), s in zip(enumerate(sids.values()), pd.unique(mapping["CRP"])):
        tg = {"numa" : n, "threads" : []}
        for t in thread_name_prefix_ru:
            tg["threads"].append(f"{t}-({'|'.join(v)})")

        for t in thread_name_prefix_tpg:
            tg["threads"].append(f"{t}-({'|'.join([str((10 * s) + j) for j in range(3)])})")

        template["thread_group"].append(tg)

    file = "pin_template_tde.json"
    with open(file, "w") as f:
        json.dump({"daq_application" : {"runp02srv004tde" : template}}, f, indent = 4)
    print(f"pinning template written to {file}")

    return

if __name__ == "__main__":
    main()