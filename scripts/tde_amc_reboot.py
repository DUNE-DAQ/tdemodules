#!/usr/bin/env python3
"""
Created on: 16/10/2025 18:27

Author: Shyam Bhuller

Description: Script to reboot AMCs from a TDE crate.
"""
import os
import time
import click

def card_slot(slotnum : int):
    return "0x%x" % (0x70+0x2*slotnum)


def reboot(mch_ip : str, slot_xp : str):
    icmd = f"ipmitool -v -I lan -H {mch_ip} -U root -P root -T 0x82 -B0 -b7"
    icard = icmd + f" -t {slot_xp} raw 0x2E 0x03 0x00 0x00 0x60"

    #? Do we ever need to use select_dune_fw and disable_flash_access?
    cmds = {
        "select_dune_fw" : " 0x40 0x40",
        "reconfigure" : " 0x8 0x8",
        "disable_flash_access" : " 0x1 0x1",
        "reboot" : " 0x8 0x0",
    }

    for c in (cmds["reconfigure"], cmds["reboot"]):
        cmd = icard + c
        print(cmd)
        os.system(cmd)
        time.sleep(1) # could make a configurable delay
    return


@click.command()
@click.argument('crate_ip', type=str)
@click.option('-s', '--slots', type=int, multiple=True, default=[i for i in range(1,13)])
def main(crate_ip : int, slots : list[int]):
    print(f"boot cards in slots {slots} in crate at {crate_ip}")

    for s in slots: 
        reboot(crate_ip, card_slot(s))
    return


if __name__=='__main__':
    main()
