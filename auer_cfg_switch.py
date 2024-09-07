#!/usr/bin/env python3
"""
AuerswaldCfgSwitcher

Author: Andreas Thienemann
License: GPLv3+
"""

import argparse
import os.path
import pprint
import requests
import sshtunnel
import time
import yaml
from rich import print as rprint
import rich.console
import rich.table


class AuerswaldCfgMgr:
    """Auerswald Config Manager"""

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.ssl_verify = False
        self.uuid = None
        self._load_config()
        self.session = requests.Session()
        self.session.auth = requests.auth.HTTPDigestAuth(
            self.auer_admin_user, self.auer_admin_pass
        )
        self.session.verify = False

        # Silence warnings if we're not doing verification
        if not self.ssl_verify:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning

            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    def _load_config(self):
        """Load the configfile"""
        file = f"{self.script_dir}/auerswald.cfg.yaml"
        with open(file, "r") as f:
            data = yaml.safe_load(f)
        for key, value in data.items():
            setattr(self, key, value)

    def _enable_debug(self):
        """Enable debug output for requests"""
        try:
            import http.client as http_client
        except ImportError:
            # Python 2
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1

        # You must initialize logging, otherwise you'll not see debug output.
        import logging

        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def _connect_ssh_tunnel(self):
        self.tunnel = sshtunnel.SSHTunnelForwarder(
            (self.ssh_host, self.ssh_port),
            ssh_username=self.ssh_user,
            ssh_password=self.ssh_pass,
            remote_bind_address=(self.auer_address, 443),
        )
        self.tunnel.start()
        return self.tunnel.local_bind_port

    def _disconnect_ssh_tunnel(self):
        self.tunnel.stop()

    def _fetch(self, path):
        """Fetch generic data drom the PBX"""
        if self.ssh_tunnel:
            url = f"https://127.0.0.1:{self.tunnel.local_bind_port}{path}"
        else:
            url = f"https://{self.auer_address}{path}"
        r = self.session.get(url)
        return r

    def _send(self, path, params=None, data=None, files=None, headers=None):
        """Post generic data to the PBX"""
        if self.ssh_tunnel:
            url = f"https://127.0.0.1:{self.tunnel.local_bind_port}{path}"
        else:
            url = f"https://{self.auer_address}{path}"
        r = self.session.post(
            url,
            params=params,
            data=data,
            files=files,
            headers=headers,
        )
        return r

    def _fetch_pbx_info(self):
        """Fetch pbx info"""
        return self._fetch("/tree").json()

    def _fetch_autoswitch_state(self):
        """Fetch autoswitch state"""
        return self._fetch("/config_autoswitch_state").json()

    def _fetch_cfg_state(self):
        """Fetch list of config"""
        return self._fetch("/configs_state").json()

    def _fetch_times_state(self):
        """Fetch list of config"""
        return self._fetch("/configs_switchtimes_state").json()

    def _pbx_product(self):
        """Return the pbx product name"""
        if not hasattr(self, "pbx_info"):
            self.pbx_info = self._fetch_pbx_info()
        return self.pbx_info[0]["pbx"]

    def _pbx_name(self):
        """Return the pbx name"""
        if not hasattr(self, "pbx_info"):
            self.pbx_info = self._fetch_pbx_info()
        return self.pbx_info[0]["pbxEdit"]

    def show_configurations(self):
        """Nicely display the current situation of the device"""

        console = rich.console.Console()
        rprint(
            f"[white][bold]{self._pbx_product()} | {self._pbx_name()}:[/bold]",
            "Zeitsteuerung [magenta]/[/magenta] Konfigurationen",
        )
        console.print()
        table = rich.table.Table(
            title="Konfigurationsumschaltung",
            show_header=False,
            show_edge=False,
            show_lines=False,
            box=None,
        )
        autoswitch_state = self._fetch_autoswitch_state()
        table.add_row(
            "Automatische Konfigurationsumschaltung",
            "[green]:heavy_check_mark:"
            if autoswitch_state["switchCfgCb"]
            else "[red]:heavy_multiplication_x:",
        )
        table.add_row(
            f"Steuerbar mit Systemrelais: {autoswitch_state['switchSysRelaisName']}",
            "[green]:heavy_check_mark:"
            if autoswitch_state["switchSysRelais"]
            else "[red]:heavy_multiplication_x:",
        )
        rprint(table)

        table = rich.table.Table(
            title="Konfigurationsnamen",
            show_header=True,
            show_edge=False,
            show_lines=False,
            box=None,
        )
        print()
        table.add_column("Konfigurationsname")
        table.add_column("Identifikationsnummer")
        configs = self._fetch_cfg_state()
        for config in configs["rows"]:
            if config.get("userdata", {}).get("active"):
                table.add_row(
                    config["data"][0], config["data"][1], "[green]:heavy_check_mark:"
                )
            else:
                table.add_row(config["data"][0], config["data"][1])
        rprint(table)

    def enable_autoswitch(self):
        """Enable Config Autoswitching"""
        current = self._fetch_autoswitch_state()
        if current["switchCfgCb"] == "1":
            return True
        data = {
            "switchCfgCb": "switchCfgCb",
            "switchSysRelais": "switchSysRelais",
            "switchSysRelaisName": current["switchSysRelaisName"],
        }
        self._send("/config_autoswitch_save", data=data)

    def disable_autoswitch(self):
        """Disable Config Autoswitching"""
        current = self._fetch_autoswitch_state()
        if current["switchCfgCb"] == "0":
            return True
        data = {
            "switchSysRelais": "switchSysRelais",
            "switchSysRelaisName": current["switchSysRelaisName"],
        }
        self._send("/config_autoswitch_save", data=data)

    def switch_config(self, cfg_number):
        configs = self._fetch_cfg_state()["rows"]
        for config in configs:
            if config["data"][1] == str(cfg_number):
                if config.get("userdata", {}).get("active"):
                    return True
                params = {"configId": str(config["id"])}
                self._send("/configs_set", params=params)
                time.sleep(1)
                return True
        print(f"Identifikationsnummer {cfg_number} not found")
        exit(1)

    def main(self):
        parser = argparse.ArgumentParser(
            description="Manage the Auerswald PBX Config Templates"
        )
        parser.add_argument(
            "command",
            choices=["show", "enable", "disable", "select"],
            help="Action to be performed.",
        )
        parser.add_argument(
            "number",
            nargs="?",
            type=int,
            help="Config to switch to, required when command is 'switch'",
        )
        parser.add_argument("--debug", action="store_true", help="Debug output.")

        args = parser.parse_args()

        if args.command == "select" and args.number is None:
            parser.error("The 'select' command requires a number.")

        if args.debug:
            self._enable_debug()

        if self.ssh_tunnel:
            self._connect_ssh_tunnel()

        if args.command == "show":
            self.show_configurations()
        elif args.command == "enable":
            self.enable_autoswitch()
            self.show_configurations()
        elif args.command == "disable":
            self.disable_autoswitch()
            self.show_configurations()
        elif args.command == "select":
            self.switch_config(args.number)
            self.show_configurations()
        else:
            print("Unsupported command")

        if self.ssh_tunnel:
            self._disconnect_ssh_tunnel()


if __name__ == "__main__":
    aw_cfg = AuerswaldCfgMgr()
    aw_cfg.main()
