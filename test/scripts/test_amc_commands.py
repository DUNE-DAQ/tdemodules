#!/usr/bin/env python


import tdemodules
import click
import time


@click.command()
def main():
    
    crate_id = 0
    slot_id = [1, 6, 7]

    controllers = []
    for s in slot_id:
        amc_ctrl_ip = f"10.73.{crate_id+32}.{s+1}"
        amc_data_port = 54321+(s+1)
        c = tdemodules.AMCController(amc_ctrl_ip, amc_data_port)
        print(f"Reading status of card {amc_ctrl_ip} (crate {crate_id}, slot {s})")
        c.card_status()
        controllers.append(c)

    for s, c in zip(slot_id, controllers):
        print(f"starting card {s}")
        c.card_start()

    print("Waiting")
    t_interval = 10
    for i in range(5):
        time.sleep(t_interval)
        print(f"-- {i*t_interval} s elapsed")
        # c.card_status()

    for s, c in zip(slot_id, controllers):
        print(f"stopping card {s}")
        c.card_stop()




if __name__ == '__main__':
    main()