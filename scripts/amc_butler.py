#!/usr/bin/env python
"""
Created on: 05/06/2025 11:16

Author: Shyam Bhuller

Description: Check the status of an AMC or multiple AMCs to ensure they can be reached.
"""

import argparse
import subprocess
import time

import tdemodules

def ping(host):
    return subprocess.call(['ping', "-c", '1', host]) == 0

class Commands():
    def __init__(self, controllers : dict):
        self.controllers = controllers

    def stop(self):
        for k, v in self.controllers.items():
            print(f"starting: {k}")
            v.card_stop()
        return

    def start(self):
        for k, v in self.controllers.items():
            print(f"starting: {k}")
            v.card_start()
        return

    def status(self):
        # Constantly get the status of the AMCs to check whether they can be accessed.
        if self.controllers:
            print("press ctrl-C to exit.")
            ti = 10
            t = time.time()
            while True:
                for k, v in self.controllers.items():
                    print(f"Reading status of AMC with IP: {k})")
                    v.card_status()
                time.sleep(ti)
                print(f"-- {time.time() - t:.2g} s elapsed")
        return


def main(args):
    # get list of amcs from the command arguments
    controllers = {}
    if args.crate:
        if not ping(args.crate): # try pinging the crate #?also do this for the AMC option?
            print(f"Could not ping uTCA Crate at IP: {args.crate}")
            exit(1)

        for i in range(10):  # 10 is the maximum number of AMCs for any given crate currently for np02. Could have an actual mapping to create the correct amount of controllers 
            ip = args.crate.rsplit(".", 1)[0] + f".{i + 1}"
            port = 54321 + (i + 1)
            controllers[ip] = tdemodules.AMCController(ip, port)
    elif args.amc:
        for i in args.amc:
            num = int(i.split(".")[-1])
            controllers[i] = tdemodules.AMCController(i, 54321 + num)
    else:
        print("You must provide either '--crate' or pass ip addresses for the AMCs to control")
        exit(1)

    cmds = Commands(controllers)
    cmd = getattr(cmds, args.command)
    cmd()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--crate", type = str, help = "IP address of crate MCH.")
    group.add_argument("-a", "--amc", type = str, nargs = "+", help = "IP address/es of AMCs.")
    parser.add_argument("--command", type = str, choices = ["start", "stop", "status"], required = True)

    args = parser.parse_args()
    print(args)
    main(args)