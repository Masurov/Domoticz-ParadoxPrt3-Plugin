# Domoticz-ParadoxPrt3-Plugin
Python plugin for Paradox Security PRT3 serial interface module

## Key Features

* Creates 1 switch device per configured zone
* Creates 2 devices per configured area
  1. 'Arm' selector switch device that tracks/changes the area arming status
  2. 'Alarm' on/off switch that tracks the area in alarm status

## Installation

Tested on Python version 3.6 & Domoticz version 3.8153.

To install:

* Go in your Domoticz directory, open the plugins directory.
* Navigate to the directory using a command line
* Run: ```git clone https://github.com/Masurov/Domoticz-ParadoxPrt3-Plugin.git```
* Restart Domoticz.

In the web UI, navigate to the Hardware page. In the hardware dropdown there will be an entry called "Paradox PRT3 serial interface".

## Updating

To update:
* Go in your Domoticz directory using a command line and open the plugins directory then the Domoticz-ParadoxPrt3-Plugin directory.
* Run: ```git pull```
* Restart Domoticz.

## Configuration

| Field | Information|
| ----- | ---------- |
| Serial Port | Dropdown to select the Serial Port the Paradox Prt3 is plugged into |
| Zone definitions | List of the zones you want to get into Domoticz |
| Area definitions | List of the areas you want to get into Domoticz |
| Pin | Code to use to arm/disarm the areas |
| Debug | When true the logging level will be much higher to aid with troubleshooting |

## Change log

| Version | Information|
| ----- | ---------- |
| 1.0 | Initial upload version |