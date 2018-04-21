from enum import IntEnum
from enum import Enum
import re

#SYSTEM EVENT
RE_SYSTEM_EVENT = re.compile(r"G(\d\d\d)N(\d\d\d)A(\d\d\d)")

class SystemEventGroup(IntEnum):
    ZONE_OK = 0
    ZONE_OPEN = 1
    ZONE_TAMPERED = 2
    ZONE_FIRE_LOOP = 3
    ARMED_WITH_MASTERCODE = 9
    ARMED_WITH_USERCODE = 10
    ARMED_WITH_KEYSWITCH = 11
    ARMED_SPECIAL = 12
    DISARMED_WITH_MASTERCODE = 13
    DISARMED_WITH_USERCODE = 14
    DISARMED_WITH_KEYSWITCH = 15
    DISARMED_AFTERALARM_WITH_MASTERCODE = 16
    DISARMED_AFTERALARM_WITH_USERCODE = 17
    DISARMED_AFTERALARM_WITH_KEYSWITCH = 18
    ALARM_CANCELLED_WITH_MASTERCODE = 19
    ARMING_CANCELED_WITH_USERCODE = 20
    ZONE_BYPASSED=23
    ZONE_IN_ALARM=24
    FIRE_ALARM=25
    ZONE_ALARM_RESTORE=26
    FIRE_ALARM_RESTORE=27
    SPECIAL_ALARM=30
    DURESS_ALARM_BY_USER=31
    ZONE_SHUTDOWN=32
    ZONE_TAMPER =33
    ZONE_TAMPER_RESTORE=34
    TROUBLE_EVENT = 36
    TROUBLE_RESTORE = 37
    MODULE_TROUBLE = 38
    MODULE_TROUBLE_RESTORE = 39
    LOW_BATTERY_ON_ZONE = 41
    ZONE_SUPERVISION_TROUBLE = 42
    LOW_BATTERY_ON_ZONE_RESTORE = 43
    ZONE_SUPERVISION_TROUBLE_RESTORE = 44
    STATUS1 = 64
    STATUS2 = 65
    STATUS3 = 66

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)


###### COMMANDS SENT TO THE MODULE FROM US
VIRTUAL_INPUT_OPEN = "VO%03d"
VIRTUAL_INPUT_CLOSED = "VC%03d"

#AREA REQUEST STATUS
REQUEST_AREA_STATUS_FORMAT = "RA{0:0>3}"
#only aera number, arm and alarm status bytes are captured
RE_REQUEST_AREA_STATUS_REPLY = re.compile(r"RA(\d\d\d)(\w)\w\w\w\w(\w)\w")

class AreaArmStatus(Enum):
    DISARMED = "D"
    ARMED = "A"
    FORCEARMED = "F"
    STAYARMED = "S"
    INSTANTARMED = "I"

class AreaAlarmStatus(Enum):
    OK = "O"
    INALARM = "A"


#ZONE REQUEST STATUS
REQUEST_ZONE_STATUS_FORMAT = "RZ{0:0>3}"
#only zone number and status bytes are captured
RE_REQUEST_ZONE_STATUS_REPLY = re.compile(r"RZ(\d\d\d)(\w)\w\w\w\w")

class ZoneStatusReply(Enum):
    CLOSED = "C"
    OPEN = "O"
    TAMPERED = "T"
    FIRELOOP = "F"

# Label requests
REQUEST_ZONE_LABEL = "ZL%03d"
REQUEST_AREA_LABEL = "AL%03d"
REQUEST_USER_LABEL = "UL%03d"

# Arm request
AREA_ARM = "AA%03d%s%s"
AREA_DISARM = "AD%03d%s"

# Panic request
EMERGENCY_PANIC = "PE%03d"
MEDICAL_PANIC = "PM%03d"
FIRE_PANIC = "PF%03d"

SMOKE_RESET = "SR%03d"

# PGM incoming request
VIRTUAL_PGM_ON = re.compile(r"PGM(\d\d)ON")
VIRTUAL_PGM_OFF = re.compile(r"PGM(\d\d)OFF")



class Event(object):
    group = None
    number = None
    area = None
    
    def __str__(self):
        return "Group '%s' Number '%s' Area '%s'" % (self.group, self.number, self.area)
    
def interprete(line):
    event_to_return = Event()

    #system event handling
    matchSystemEvent = RE_SYSTEM_EVENT.match(line)
    if matchSystemEvent:
        group, number, area = matchSystemEvent.groups()
        group = int(group)
        number = int(number)
        area = int(area)

        if not SystemEventGroup.has_value(group):
            return None

        event_to_return.group = group
        event_to_return.number = number
        event_to_return.area = area
        return { event_to_return }

    #zone request reply, convert it to an equivalent system event
    matchZoneRequestReply = RE_REQUEST_ZONE_STATUS_REPLY.match(line)
    if matchZoneRequestReply:
        zonestate = matchZoneRequestReply.groups()[1]
        if (zonestate == ZoneStatusReply.CLOSED.value) :
            event_to_return.group = SystemEventGroup.ZONE_OK
        elif(zonestate == ZoneStatusReply.OPEN.value):
            event_to_return.group = SystemEventGroup.ZONE_OPEN
        elif(zonestate == ZoneStatusReply.TAMPERED.value):
            event_to_return.group = SystemEventGroup.ZONE_TAMPERED
        elif(zonestate == ZoneStatusReply.FIRELOOP.value):
            event_to_return.group = SystemEventGroup.ZONE_FIRE_LOOP
        else:
            return None

        #zone
        event_to_return.number = (int)(matchZoneRequestReply.groups()[0])
        return { event_to_return }

    #area request reply, convert it to an equivalent system event
    matchAreaRequestReply = RE_REQUEST_AREA_STATUS_REPLY.match(line)
    if matchAreaRequestReply:
        
        #area
        areaNumber = (int)(matchAreaRequestReply.groups()[0])


        areaArmEvent = Event()
        areaArmEvent.area = areaNumber

        areaAlarmEvent = Event()
        areaAlarmEvent.area = areaNumber

        #arm state
        areaarmstate = matchAreaRequestReply.groups()[1]
        if (areaarmstate == AreaArmStatus.DISARMED.value) :
            areaArmEvent.group = SystemEventGroup.DISARMED_WITH_USERCODE
        else :
            areaArmEvent.group = SystemEventGroup.ARMED_WITH_USERCODE

        #alarm state
        areaalarmstate = matchAreaRequestReply.groups()[2]
        if (areaalarmstate == AreaAlarmStatus.OK.value) :
            areaAlarmEvent.group = SystemEventGroup.ZONE_ALARM_RESTORE
        elif(areaalarmstate == AreaAlarmStatus.INALARM.value):
            areaAlarmEvent.group = SystemEventGroup.ZONE_IN_ALARM
        else :
            return { areaArmEvent }

        return { areaArmEvent, areaAlarmEvent}

    return None