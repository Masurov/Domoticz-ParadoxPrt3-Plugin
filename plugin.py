#           Paradox PRT3 serial interface Plugin
#
#           Author:     Masure, 2018
#
#
#   Plugin parameter definition below will be parsed during startup and copied into Manifest.xml, this will then drive the user interface in the Hardware web page

"""
<plugin key="ParadoxPrt3" name="Paradox PRT3 serial interface" author="Masure" version="1.0" externallink="">
    <params>
        <param field="SerialPort" label="Serial Port" width="150px" required="true" default="COM7"/>
        <param field="Mode1" label="Zone definitions (paradox zone number#label|...)" width="400px" required="true" default="1#Motion Kitchen|2#Motion Hall|3#Motion Outdoors" />
        <param field="Mode2" label="Area definitions (paradox area number#label|...)" width="400px" required="true" default="1#House|2#Outside"/>
        <param field="Mode3" label="Pin" width="80px" required="true" />
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import ParadoxCst

SerialConn = None
hasConnected = False
deviceDiscoveryDone = False
serialBuffer = ""

def onStart():
    global SerialConn, deviceDiscoveryDone

    deviceDiscoveryDone = False

    if Parameters["Mode6"] != "Normal":
        Domoticz.Debugging(1)

    Domoticz.Log("Plugin has " + str(len(Devices)) + " devices associated with it.")
    DumpConfigToLog()
    for Device in Devices:
        Devices[Device].Update(nValue=Devices[Device].nValue, sValue=Devices[Device].sValue)
    SerialConn = Domoticz.Connection(Name="PRT3", Transport="Serial", Protocol="line", Address=Parameters["SerialPort"], Baud=57600)
    SerialConn.Connect()
    return

def CreateDevices():

    #zones
    for zoneParam in Parameters["Mode1"].split("|"):
        paradoxZoneId = zoneParam.split("#")[0]
        zoneDeviceLabel = zoneParam.split("#")[1]

        if (GetZoneDevice(paradoxZoneId) == None):
            LogMessage("Creating zone " + paradoxZoneId)
            Domoticz.Device(Name=zoneDeviceLabel, Unit=getNextDeviceId(), TypeName="Switch", Switchtype=11, DeviceID="Z"+paradoxZoneId.zfill(3)).Create()
        else:
            LogMessage("Device already exists for Zone " + paradoxZoneId + " (" + zoneDeviceLabel + ")")

    #areas
    for areaParam in Parameters["Mode2"].split("|"):
        paradoxAreaId = areaParam.split("#")[0]
        areaDeviceLabel = areaParam.split("#")[1]

        if (GetAreaArmDevice(paradoxAreaId) == None):
            #Area status switchtype 18 selector 
            Options = {"LevelActions": "||||", "LevelNames": "Désarmé|Armé|Armé (forcé)|Armé (partiel)|Armé (instantané)", "LevelOffHidden": "false", "SelectorStyle": "1"}
            Domoticz.Device(Name="[Armement] " + areaDeviceLabel, Unit=getNextDeviceId(), TypeName="Selector Switch", Switchtype=18, DeviceID="AAR"+paradoxAreaId.zfill(3), Options=Options).Create()
        else:
            LogMessage("Arm Device already exists for Area " + paradoxAreaId + " (" + areaDeviceLabel + ")")

        if (GetAreaAlarmDevice(paradoxAreaId) == None):
            Domoticz.Device(Name="[Alarme] " + areaDeviceLabel, Unit=getNextDeviceId(), TypeName="Switch", Switchtype=8, DeviceID="AAL"+paradoxAreaId.zfill(3)).Create()
        else:
            LogMessage("Alarm Device already exists for Area " + paradoxAreaId + " (" + areaDeviceLabel + ")")

def getNextDeviceId():
    nextDeviceId = 1

    while True:
        exists = False
        for device in Devices:
            if (device == nextDeviceId) :
                exists = True
                break
        if (not exists):
            break;
        nextDeviceId = nextDeviceId + 1

    return nextDeviceId

def onConnect(Connection, Status, Description):
    global SerialConn, deviceDiscoveryDone
    
    if (Status == 0):
        LogMessage("Connected successfully to: "+Parameters["SerialPort"])
        SerialConn = Connection

        if (not deviceDiscoveryDone):
            CreateDevices()
            deviceDiscoveryDone = True

        RequestUpdate()
    else:
        LogMessage("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"])
        Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["SerialPort"]+" with error: "+Description)
    return True

def RequestUpdate():

    for device in Devices:

        if (Devices[device].DeviceID.startswith("Z")):
            zoneId = (int)(Devices[device].DeviceID[1:])
            LogMessage("Requesting Zone {0} status".format(zoneId))
            Send(ParadoxCst.REQUEST_ZONE_STATUS_FORMAT.format(zoneId), False)

        if (Devices[device].DeviceID.startswith("AAR")):
            areaId = (int)(Devices[device].DeviceID[3:])
            LogMessage("Requesting Area {0} status".format(areaId))
            Send(ParadoxCst.REQUEST_AREA_STATUS_FORMAT.format(areaId), False)
    
    return 

def Send(message, log):
    
    if (log == True):
        LogMessage("Sending [{0}]".format(message))

    SerialConn.Send(message + "\r")

    if (log == True):
        LogMessage("Sent [{0}]".format(message))

def onMessage(Connection, Data):
    global hasConnected, serialBuffer
    
    serialBuffer  += Data.decode("ascii")
    
    messages = serialBuffer.split("\r")
    i = 0
    while (i < len(messages) - 1):
        strData = messages[i]
        processMessage(strData)
        i += 1

    serialBuffer = messages[len(messages) - 1]


def processMessage(strData):

    events = ParadoxCst.interprete(strData)
    if (events == None):
        if (True) :
            LogMessage("Received [{0}] unhandled event".format(strData.replace("\r", "<cr>")))
    else :
        if (True) :
            LogMessage("Received [{0}] handling ...".format(strData.replace("\r", "<cr>")))
        EventUpdateDevice(events)

#Event groups defining disarming
GROUPS_DISARMED = {ParadoxCst.SystemEventGroup.DISARMED_WITH_MASTERCODE,
                    ParadoxCst.SystemEventGroup.DISARMED_WITH_USERCODE,
                    ParadoxCst.SystemEventGroup.DISARMED_WITH_KEYSWITCH,
                    ParadoxCst.SystemEventGroup.DISARMED_AFTERALARM_WITH_MASTERCODE,
                    ParadoxCst.SystemEventGroup.DISARMED_AFTERALARM_WITH_USERCODE,
                    ParadoxCst.SystemEventGroup.DISARMED_AFTERALARM_WITH_KEYSWITCH
                    }

#Event groups defining arming
GROUPS_ARMED = {ParadoxCst.SystemEventGroup.ARMED_WITH_MASTERCODE,
                ParadoxCst.SystemEventGroup.ARMED_WITH_USERCODE,
                ParadoxCst.SystemEventGroup.ARMED_WITH_KEYSWITCH,
                ParadoxCst.SystemEventGroup.ARMED_SPECIAL
                }

#Event groups defining alarm
GROUPS_ALARMON = {  ParadoxCst.SystemEventGroup.ZONE_IN_ALARM,
                    ParadoxCst.SystemEventGroup.FIRE_ALARM
                    }

#Event groups defining alarm off
GROUPS_ALARMOFF = {  ParadoxCst.SystemEventGroup.ZONE_ALARM_RESTORE,
                    ParadoxCst.SystemEventGroup.FIRE_ALARM_RESTORE
                    }

#Event groups defining an open zone
GROUPS_ZONEOPEN = {  ParadoxCst.SystemEventGroup.ZONE_OPEN,
                    ParadoxCst.SystemEventGroup.ZONE_TAMPERED,
                    ParadoxCst.SystemEventGroup.ZONE_FIRE_LOOP
                    }

#Arm Domoticz selector values
ARM_SELECTOR_LEVEL_DISARMED = 0
ARM_SELECTOR_LEVEL_ARMED = 10
ARM_SELECTOR_LEVEL_FORCEDARMED = 20
ARM_SELECTOR_LEVEL_PARTIALARMED = 30
ARM_SELECTOR_LEVEL_INSTANTARMED = 40

#Arm Domoticz selector values
ARMING_MODE_CODES = {ARM_SELECTOR_LEVEL_DISARMED : None,
                     ARM_SELECTOR_LEVEL_ARMED: "A", 
                    ARM_SELECTOR_LEVEL_FORCEDARMED: "F",
                    ARM_SELECTOR_LEVEL_PARTIALARMED: "S",
                    ARM_SELECTOR_LEVEL_INSTANTARMED: "I"}

def EventUpdateDevice(events):

    for event in events :

        #zone open
        if (event.group == ParadoxCst.SystemEventGroup.ZONE_OK):
            device = GetZoneDevice(event.number)
        
            if (device == None) :
                LogMessage("Zone device not found for event : " + event.__str__())
                return

            device.Update(nValue=0, sValue="Fermé")
            return;

        #zone close
        if (event.group in GROUPS_ZONEOPEN):
            device = GetZoneDevice(event.number)
        
            if (device == None) :
                LogMessage("Zone device not found for event : " + event.__str__())
                return

            device.Update(nValue=1, sValue="Ouvert")
            return;

        #area disarmed
        if (event.group in GROUPS_DISARMED):
            device = GetAreaArmDevice(event.area)

            if (device == None) :
                LogMessage("Area device not found for event : " + event.__str__())
                return

            device.Update(nValue=0,  sValue="0")
    
        #area armed
        if (event.group in GROUPS_ARMED):
            device = GetAreaArmDevice(event.area)

            if (device == None) :
                LogMessage("Area device not found for event : " + event.__str__())
                return

            device.Update(nValue=1,  sValue="10")

                
        #area alarm ON
        if (event.group in GROUPS_ALARMON):
            device = GetAreaAlarmDevice(event.area)
    
            if (device == None) :
                LogMessage("Area device not found for event : " + event.__str__())
                return

            device.Update(nValue = 1, sValue = "Alarme")
            return

        #area alarm OFF
        if (event.group in GROUPS_ALARMOFF):
            device = GetAreaAlarmDevice(event.area)
    
            if (device == None) :
                LogMessage("Area device not found for event : " + event.__str__())
                return

            device.Update(nValue = 0, sValue = "Ok")
            return

    return

def onCommand(Unit, Command, Level, Hue):

    LogMessage("UNit {0} Command {1} Level {2} Hue {3}".format(Unit, Command, Level, Hue))

    if (not Devices[Unit].DeviceID.startswith("AAR")):
        return

    if (not Level in ARMING_MODE_CODES):
        return
        
    areaNumber = (int)(Devices[Unit].DeviceID[3:])
    if (Level == ARM_SELECTOR_LEVEL_DISARMED):
        LogMessage("Disarm")
        serialCommand = "AD{0:0>3}{1}".format(areaNumber, Parameters["Mode3"])
    else:
        serialCommand = "AA{0:0>3}{1}{2}".format(areaNumber, ARMING_MODE_CODES[Level], Parameters["Mode3"])
    
    Send(serialCommand, True)

def GetZoneDevice(paradoxZoneId):
    for device in Devices:
        if (Devices[device].DeviceID == "Z{0:0>3}".format(paradoxZoneId)) :
            return Devices[device]
    return None

def GetAreaArmDevice(paradoxAreaId):
    for device in Devices:
        if (Devices[device].DeviceID == "AAR{0:0>3}".format(paradoxAreaId)) :
            return Devices[device]
    return None

def GetAreaAlarmDevice(paradoxAreaId):
    for device in Devices:
        if (Devices[device].DeviceID == "AAL{0:0>3}".format(paradoxAreaId)) :
            return Devices[device]
    return None

def onDisconnect(Connection):
    for device in Devices:
        Devices[device].Update(nValue=Devices[device].nValue, sValue=Devices[device].sValue)
    LogMessage("Connection '"+Connection.Name+"' disconnected.")
    return

def onHeartbeat():
    global hasConnected, SerialConn
    if (not SerialConn.Connected()):
        hasConnected = False
        SerialConn.Connect()
    return True

# Generic helper functions
def LogMessage(Message):
    if Parameters["Mode6"] == "File":
        f = open(Parameters["HomeFolder"]+"plugin.log","a")
        f.write(Message+"\r\n")
        f.close()
    Domoticz.Debug(Message)

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            LogMessage( "'" + x + "':'" + str(Parameters[x]) + "'")
    LogMessage("Device count: " + str(len(Devices)))
    for x in Devices:
        LogMessage("Device:           " + str(x) + " - " + str(Devices[x]))
        LogMessage("Device ID:       '" + str(Devices[x].ID) + "'")
        LogMessage("Device Name:     '" + Devices[x].Name + "'")
        LogMessage("Device nValue:    " + str(Devices[x].nValue))
        LogMessage("Device sValue:   '" + Devices[x].sValue + "'")
        LogMessage("Device LastLevel: " + str(Devices[x].LastLevel))
    return

