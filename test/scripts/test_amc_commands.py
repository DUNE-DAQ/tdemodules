#!/usr/bin/env python


import tdemodules
import click
import time


@click.command()
def main():
    
    crate_id = 0
    slot_id = 1

    amc_ctrl_ip = f"10.73.{crate_id+32}.{slot_id+1}"
    amc_ctrl_port = 54321+(slot_id+1)
    c = tdemodules.AMCController(amc_ctrl_ip, amc_ctrl_port)
    print(f"Reading status of card {amc_ctrl_ip} (crate {crate_id}, slot {slot_id})")
    c.card_status()

    print(f"starting card {slot_id}")
    c.card_start()
    print("Waiging")
    for i in range(5):
        time.sleep(10)
        print(f"-- {i*10} s elapsed")
        c.card_status()

    print(f"stopping card {slot_id}")
    c.card_stop()




if __name__ == '__main__':
    main()