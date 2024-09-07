# Auerswald Configuration Manager

Command-line client for the Auerswald PBX Configuration Switching system

Allows connecting to the PBX via a dynamic SSH tunnel for remote access.

## Installation

Clone the repo, install the requirements using pip:

```
git clone https://github.com/ixs/AuerswaldCfgMgr.git
cd AuerswaldCfgMgr
pip install -r requirements.txt
```

## Configuration

Rename `auerswald.cfg.yaml.sample` to `auerswald.cfg.yaml` and add your site specific details.

## Example

```
$ ./auer_cfg_switch.py show
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
