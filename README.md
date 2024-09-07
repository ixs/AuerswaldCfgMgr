# Auerswald Configuration Manager

Command-line client for the Auerswald PBX Configuration Switching system

Allows connecting to the PBX via a dynamic SSH tunnel for remote access.

## Installation

Clone the repo, install the requirements using pip:

```shell
git clone https://github.com/ixs/AuerswaldCfgMgr.git
cd AuerswaldCfgMgr
pip install -r requirements.txt
```

## Configuration

Rename `auerswald.cfg.yaml.sample` to `auerswald.cfg.yaml` and add your site specific details.

## Example

```
$ ./auer_cfg_mgr.py --help
usage: auer_cfg_mgr.py [-h] [--debug] {show,enable,disable,select} [number]

Manage the Auerswald PBX Config Templates

positional arguments:
  {show,enable,disable,select}
                        The action to be performed:
                        show - Show current configuration
                        enable - Enable automatic switching
                        disable - Disable automatic switching
                        select - Manually select and activate a config
  number                Config to switch to, required when command is 'select'

options:
  -h, --help            show this help message and exit
  --debug               Debug output.
$
```

```
$ ./auer_cfg_mgr.py show
COMpact 5200R | Apotheke: Zeitsteuerung / Konfigurationen

              Konfigurationsumschaltung
 Automatische Konfigurationsumschaltung            ✔
 Steuerbar mit Systemrelais: Aut.Konfig.um. (900)  ✔

              Konfigurationsnamen
 Konfigurationsname   Identifikationsnummer
 EA Offen / SM Offen  201                    ✔
 EA Offen / SM Zu     202
 EA Zu / SM Offen     203
 EA Zu / SM Zu        204
$
```
