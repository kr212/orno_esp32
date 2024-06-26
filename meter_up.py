from machine import UART, Pin
import mqtt
import time

import paho.mqtt.client as mqtt
import json

import utils
import orno_up

BROKER='192.168.1.10'
PORT=1883

#topics
PREF='meter_test/'
STATUS=PREF+'status'
CONTROL=PREF+'control'
DATA=PREF+'data'
TX_PIN=25
RX_PIN=32
CTRL_PIN=33



#summer and winter ivtervals for G13 tariff in Poland
SUMMER_INTERVAL=[(datetime.time(0,0),3),(datetime.time(7,0),1),(datetime.time(13,0),3),(datetime.time(19,0),2),(datetime.time(22,0),3)]
WINTER_INTERVAL=[(datetime.time(0,0),3),(datetime.time(7,0),1),(datetime.time(13,0),3),(datetime.time(16,0),2),(datetime.time(21,0),3)]
HOLIDAY_INTERVAL=[(datetime.time(0,0),3)]
SUMMER_START=datetime.date(2000,4,1)
WINTER_START=datetime.date(2000,10,1)
#interval between reads
INTERVAL=datetime.timedelta(seconds=2)


#-------------------------------------------------------------------

#mqtt client
client=mqtt.MQTTClient('meter_house',BROKER,PORT)



connected=False

#try to connect until connected
while not connected:
    try:
        #try connecting
        client.connect()
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
        port=UART.init(1,9600,parity=0,tx=TX_PIN,rx=RX_PIN,timeout=900) 
    except:
        #error during opening port
        time.sleep(10)
    else:
        connected=True


#create meter object
meter=orno_up.Meter(port,1,CTRL_PIN)
reg_tmp=meter.get_reg_names('work')

#create aliases dictionary, for backward compatibility (many other scripts uses old names)
registers={}
for reg in reg_tmp:
    registers[reg]=reg

registers['Total Active Power']='power_mom'
registers['Total Active Energy']='power'
registers['T1 Total Active Energy']='power_T1'
registers['T2 Total Active Energy']='power_T2'
registers['T3 Total Active Energy']='power_T3'


lines=len(registers.keys())

print(f'Time updated : {meter.sync_time()}')


#check the holiday at startup
now=time.time()
tim=time.localtime(now)


if utils.is_holiday(now):
    summer=time.mktime((tim.tm_year,SUMMER_START.tm_mon,SUMMER_START.tm_mday,0,0,0,0,1,-1))
    winter=time.mktime((tim.tm_year,WINTER_START.tm_mon,WINTER_START.tm_mday,0,0,0,0,1,-1))

    if (now>=summer and now<winter):
        int_to_change=1
    else:
        int_to_change=2
    
    holiday=now+120 #next 2 minutes 
    meter.set_interval(int_to_change,[(holiday,3)])
    set_in_meter='hol'
    print('Set holiday tariff in meter')
else:
    meter.set_interval(1,SUMMER_INTERVAL)
    meter.set_interval(2,WINTER_INTERVAL)
    set_in_meter='ord'
    print('Set standard tariff in meter')


#read data from OR-WE_517 meter
#set previous time
previous_read_time=time.time()
#was the time in the meter checked?
time_checked=False
minute_of_time_check=1
holiday_checked=False


#MAIN LOOP-----------------------------------------------------------------
while True:
    client.publish(STATUS,f'{utils.now()}: Meter running')
    #send queries for all type off data
    for query in registers:
        read_f=meter.read(query)

        
        #publish
        pub_valid=utils.t_s(time.time()+2*INTERVAL) #how long data is valid, need this for storage
        data=json.dumps({'time':utils.now(),'value':round(read_f,2),'valid':pub_valid})
        #is an alias for topic name?
        client.publish(f'{DATA}/{registers[query]}',data)

        print(f"Published: {registers[query]:25} : {read_f:.2f}")
        
    

    time_now=time.localtime()
    time_now_s=time.mktime(time_now)
    #check time inside the meter every 1 minute past an hour
    if (time_now.tm_min==minute_of_time_check) and (not time_checked):
        print(f'Time updated : {meter.sync_time()}')
        time_checked=True
    elif (time_now.tm_min!=minute_of_time_check):
        time_checked=False


    #check if it is a holiday day and change interval in the meter, always at 01:05
    if ((time_now.tm_min==5) and (time_now.tm_hour==1)) and (not holiday_checked):
        holiday_checked=True
        print('Holiday check')
        if (utils.is_holiday(time_now_s)) and (set_in_meter=='ord'):
            summer=time.mktime((time_now.tm_year,SUMMER_START.tm_mon,SUMMER_START.tm_mday,0,0,0,0,1,-1))
            winter=time.mktime((time_now.tm_year,WINTER_START.tm_mon,WINTER_START.tm_mday,0,0,0,0,1,-1))

            if (time_now_s>=summer and time_now_s<winter):
                int_to_change=1
            else:
                int_to_change=2

            holiday=time_now_s+120
            meter.set_interval(int_to_change,[(holiday,3)])
            set_in_meter='hol'
            print('Set holiday tariff in meter')
        elif (not utils.is_holiday(time_now_s)) and (set_in_meter=='hol'):
            meter.set_interval(1,SUMMER_INTERVAL)
            meter.set_interval(2,WINTER_INTERVAL)
            set_in_meter='ord'
            print('Set standard tariff in meter')
    elif (time_now.tm_min!=5) or (time_now.tm_hour!=1):
        holiday_checked=False
        
    #print(meter.get_interval(1))
    #print(meter.get_interval(2))
    #print(meter.get_zone())

    #time update
    time_now=time.time()
    #does the time between data reeds is to short?
    cycle_too_short=True
    #read after an interval
    while ((time_now-previous_read_time)<INTERVAL):
        #there was at least 1 loop execution
        cycle_too_short=False
        #print('czekam')
        #wait
        time.sleep(0.1)
        time_now=time.time()
    if cycle_too_short:
        client.publish(STATUS,f'{utils.now()}: Cycle too short')
        print(f"Cycle too short!")
    #previous time set to now
    previous_read_time=time_now
    







