import secrets
#import mqtt_pub_params
import net_connect
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led, Button
from machine import Pin
import utime
import machine
from umqttsimple import MQTTClient

def reset_pico():
   print('Bailing out with a machine soft reset...')
   time.sleep(1)
   wifi_led.off()
   machine.soft_reset()
   
def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection


count=0
count_h=0
ip = '0'
wifi_led = Pin(27, Pin.OUT) #WiFi connected
alarm_led = Pin(13, Pin.OUT) #leak detected
btn1 = Button(15)
wifi_led.off()

sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

ip = net_connect.connect(secrets.SSID, secrets.PASSWORD)
if ip != "-1":
    print("connected on :" + ip)
    wifi_led.on()
    #connection = open_socket(ip)
else:
    reset_pico()

while True:
    if btn1.is_pressed:
        print("button 1 is closed")
        alarm_led.toggle()
    else:
        #print("button 1 is open")
        alarm_led.off()
            
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature_c = 27 - (reading - 0.706)/0.001721
    fahrenheit_degrees = temperature_c * (9 / 5) + 32
    Temp_F = "Pico Temperature: " + str(round(fahrenheit_degrees,2)) + " *F"
    #print(Temp_F)
    utime.sleep(1)
    

