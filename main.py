from machine import UART, Pin, soft_reset, WDT, freq, RTC, Timer
from requests import get
import network
import mqtt
import time
import json
import ntptime

import utils_up
import orno_up

BROKER='192.168.1.10'
PORT=1883
IP='192.168.1.31'

#topics
PREF='meter_test/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'
TX_PIN=32
RX_PIN=33
CTRL_PIN=25



#summer and winter ivtervals for G13 tariff in Poland
SUMMER_INTERVAL=[(time.mktime((2000,1,1,0,0,0,0,1)),3),(time.mktime((2000,1,1,7,0,0,0,1)),1),(time.mktime((2000,1,1,13,0,0,0,1)),3),(time.mktime((2000,1,1,19,0,0,0,1)),2),(time.mktime((2000,1,1,22,0,0,0,1)),3)]
WINTER_INTERVAL=[(time.mktime((2000,1,1,0,0,0,0,1)),3),(time.mktime((2000,1,1,7,0,0,0,1)),1),(time.mktime((2000,1,1,13,0,0,0,1)),3),(time.mktime((2000,1,1,16,0,0,0,1)),2),(time.mktime((2000,1,1,21,0,0,0,1)),3)]
HOLIDAY_INTERVAL=[(time.mktime((2000,1,1,0,0,0,0,1)),3)]
SUMMER_START=time.mktime((2000,4,1,0,0,0,0,1))
WINTER_START=time.mktime((2000,10,1,0,0,0,0,1))
#interval between reads
INTERVAL=int(2) #seconds
ALARM_INTERVAL=3600

rtc=RTC()
ntptime.host='ntp.nask.pl'

def time_sync_ntp():
    """synchronise rtc time with ntp server and set timezone from worldtimeapi"""
    req=get('https://worldtimeapi.org/api/timezone/Europe/Warsaw')
    #'utc_offset':'+02:00'
    offset=int(req.json()['utc_offset'].split(':')[0])    #create int
    ntptime.settime()
    global rtc
    
    UTC=utils_up.stime()  #time in seconds
    local=UTC+offset*3600
    local_tuple=time.localtime(local)
    rtc.datetime((local_tuple[0],local_tuple[1],local_tuple[2],local_tuple[6],local_tuple[3],local_tuple[4],local_tuple[5],0))
    return f'RTC time set to: {rtc.datetime()}'


# def time_sync():
#     """synchronise rtc time with ntp server and set timezone from worldtimeapi"""
#     req=get('http://worldtimeapi.org/api/timezone/Europe/Warsaw')
#     #'utc_offset':'+02:00'
#     date_str=req.json()['datetime']
#     year=int(date_str[:4])
#     month=int(date_str[5:7])
#     day=int(date_str[8:10])
#     hour=int(date_str[11:13])
#     minute=int(date_str[14:16])
#     second=int(date_str[17:19])
#     micro=int(date_str[20:26])
#     w_day=int(req.json()['day_of_week'])-1
    
#     print(year,month,day,hour,minute,second,micro)
#     rtc.datetime((year,month,day,w_day,hour,minute,second,micro))
#     print('RTC time set to:',rtc.datetime())
#     time.sleep(100)
#     #ntptime.settime(timezone=2,'ntp.nask.pl')

def holiday_check():
    """check if there is a holiday day and change interval to measure only 3rd tariff that day"""
    time_now=time.localtime()
    time_now_s=time.mktime(time_now)
    global set_in_meter
    print('Holiday check')
    if (utils_up.is_holiday(time_now_s) and (set_in_meter!='hol')):
        tmp_time=time.localtime(SUMMER_START)
        summer=time.mktime((time_now_s[0],tmp_time[1],tmp_time[2],0,0,0,0,1))
        tmp_time=time.localtime(WINTER_START)
        winter=time.mktime((time_now_s[0],tmp_time[1],tmp_time[2],0,0,0,0,1))

        if (time_now_s>=summer and time_now_s<winter):
            int_to_change=1
        else:
            int_to_change=2
        
        holiday=time_now_s+120 #next 2 minutes 
        meter.set_interval(int_to_change,[(holiday,3)])
        set_in_meter='hol'
        return 'Set holiday tariff in meter'
    elif (not utils_up.is_holiday(time_now_s)) and (set_in_meter!='ord'):
        meter.set_interval(1,SUMMER_INTERVAL)
        meter.set_interval(2,WINTER_INTERVAL)
        set_in_meter='ord'
        return 'Set standard tariff in meter'



#put everything in try..except to make sure that esp will restart in case of eny exception
#try:

#-------------------------------------------------------------------MAIN--

freq(240000000)

error=False   #global error - restart all
print('Waiting...')
time.sleep(5)
print(time_sync_ntp())   #sync the time with ntp server
#time.sleep(10)    #temporary

#control LED
led_pin=Pin(2,Pin.OUT)

#what ind of day is set in meter
set_in_meter='none'




#mqtt client
client=mqtt.MQTTClient('meter_house',BROKER,PORT,keepalive=10000)



connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        print('Connecting MQTT...')
        client.connect(clean_session=False)
    except:
        time.sleep(10)
    else:
        connected=True



#rs485
connected=False


while not connected:
    #open serial port
    try:
        #open port
        print('Connecting UART...')
        #port=UART.init(1,9600,parity=0,tx=TX_PIN,rx=RX_PIN,timeout=900)
        port=UART(2,baudrate=9600,parity=0,tx=TX_PIN,rx=RX_PIN,timeout=900,timeout_char=1)
        
    except Exception as e:
        #error during opening port
        print(e)
        time.sleep(10)
    else:
        connected=True


#create meter object
meter=orno_up.Meter(port,1,CTRL_PIN)
registers=meter.get_reg_names('work')



lines=len(registers)

#check the time in meter
print(f'Time updated in meter: {meter.sync_time()}')

#check the holiday at startup
print(holiday_check())


#read data from OR-WE_517 meter
#set previous time
previous_read_time=utils_up.stime()
#was the time in the meter checked?
time_checked=False
minute_of_time_check=5
holiday_checked=False


#MAIN LOOP-----------------------------------------------------------------
while True:
    now=time.ticks_ms()
    client.publish(STATUS,f'{utils_up.now()}: Meter running')
    
    #send queries for all type off data
    for query in registers:
        led_pin.on()
        read_f=meter.read(query)
        led_pin.off()
        

        
        #publish
        pub_valid=utils_up.t_s(utils_up.stime()+2*INTERVAL) #how long data is valid, need this for storage
        data=json.dumps({'time':utils_up.now(),'value':round(read_f,2),'valid':pub_valid})

        client.publish(f'{DATA}/{query}',data)
        

        print(f"Published: {query:25} : {read_f:.2f}")
        
    

    time_now=time.localtime()
    time_now_s=time.mktime(time_now)
    #time_now is tuple (year, month, mday, hour, minute, second, weekday, yearday)
    #check time inside the meter every 5 minutes past an hour, also check ntp time and holiday
    if (time_now[0]==minute_of_time_check) and (not time_checked):
        #add time synchronization from NTP
        #synchronise RTC time with worldtimeapi
        print(time_sync_ntp())
        print(f'Time updated in meter: {meter.sync_time()}')
        print(holiday_check())
        time_checked=True
    elif (time_now[0]!=minute_of_time_check):
        time_checked=False


    # #check if it is a holiday day and change interval in the meter, always at 01:05
    # if ((time_now[4]==5) and (time_now[3]==1)) and (not holiday_checked):
    #     holiday_checked=True
    #     print('Holiday check')
    #     if (utils_up.is_holiday(time_now_s)) and (set_in_meter=='ord'):
    #         tmp_time=time.localtime(SUMMER_START)
    #         summer=time.mktime((time_now[0],tmp_time[1],tmp_time[2],0,0,0,0,1))
    #         tmp_time=time.localtime(WINTER_START)
    #         winter=time.mktime((time_now[0],tmp_time[1],tmp_time[2],0,0,0,0,1))

    #         if (time_now_s>=summer and time_now_s<winter):
    #             int_to_change=1
    #         else:
    #             int_to_change=2

    #         holiday=time_now_s+120
    #         meter.set_interval(int_to_change,[(holiday,3)])
    #         set_in_meter='hol'
    #         print('Set holiday tariff in meter')
    #     elif (not utils_up.is_holiday(time_now_s)) and (set_in_meter=='hol'):
    #         meter.set_interval(1,SUMMER_INTERVAL)
    #         meter.set_interval(2,WINTER_INTERVAL)
    #         set_in_meter='ord'
    #         print('Set standard tariff in meter')
    # elif (time_now[4]!=5) or (time_now[3]!=1):
    #     holiday_checked=False
        
    #print(meter.get_interval(1))
    #print(meter.get_interval(2))
    #print(meter.get_zone())

    
    print(f'Execution time: {time.ticks_ms()-now} ms')
    #time update
    time_now=utils_up.stime()
    #does the time between data reeds is to short?
    cycle_too_short=True
    #read after an interval
    while ((time_now-previous_read_time)<INTERVAL):
        #there was at least 1 loop execution
        cycle_too_short=False
        #print('czekam')
        #wait
        time.sleep(0.1)
        time_now=utils_up.stime()
    if cycle_too_short:
        client.publish(STATUS,f'{utils_up.now()}: Cycle too short')
        print(f"Cycle too short!")
    #previous time set to now
    previous_read_time=time_now

    #end while------------------------
#except KeyboardInterrupt:
#    raise
#except Exception as es:
#    print(es)
#    soft_reset()
