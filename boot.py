# This file is executed on every boot (including wake-boot from deepsleep)
import esp
esp.osdebug(None)
#import webrepl
#webrepl.start()
import network

file=open('wifi_pass','r')
ssid=file.readline().rstrip()
password=file.readline().rstrip()
file.close()

wlan=network.WLAN(network.STA_IF)
wlan.active(True)

if not wlan.isconnected():
    wlan.connect(ssid,password)
    while not wlan.isconnected():
        pass
    print(wlan.ifconfig())

