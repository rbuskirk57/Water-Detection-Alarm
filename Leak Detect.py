import secrets
#import mqtt_pub_params
import net_connect
import socket
from time import sleep
#from picozero import pico_temp_sensor, pico_led, Button
from machine import Pin, PWM
import utime
import machine
from umqttsimple import MQTTClient
import math

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

def pulse(l, t):
    for i in range(10):
        l.duty_u16(int(math.sin(i / 10 * math.pi) * 500 + 500))
        utime.sleep_ms(t)
        
count=0
count_h=0
ip = '0'
wifi_led = Pin(27, Pin.OUT) #WiFi connected
alarm_led = Pin(13, Pin.OUT) #leak detected RED or sensor not connected
Sensor_1_OK_led = Pin(12, Pin.OUT) # Green if OK; Red if not
Sensor_1 = Pin(15, Pin.IN, Pin.PULL_UP)
Sensor_1_OK = Pin(14, Pin.IN, Pin.PULL_UP) # Sensor detected

buzzer = PWM(Pin(19), freq=700)
wifi_led.off()

#pulse(buzzer, 10)
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

ip = net_connect.connect(secrets.SSID, secrets.PASSWORD)
if ip != "-1":
    print("connected on :" + ip)
    wifi_led.on()
else:
    reset_pico()

while True:
    #print("OK: " + str(Sensor_1_OK.value()))
    if Sensor_1_OK.value():
        #Leak detected
        if not Sensor_1.value():
            alarm_led.toggle()
            Sensor_1_OK_led.on() # GREEN OFF
            #pulse(buzzer, 25)
            buzzer.duty_u16(32768) 
        else: # No Leak Sensor Detected
            Sensor_1_OK_led.off() # GREEN
            alarm_led.on()
            buzzer.duty_u16(0)
    else:
        # No Sensor Detected
        alarm_led.off() # RED ON
        Sensor_1_OK_led.on() # GREEN OFF
        buzzer.duty_u16(0) # turn off the buzzer
            
    reading = sensor_temp.read_u16() * conversion_factor 
    temperature_c = 27 - (reading - 0.706)/0.001721
    fahrenheit_degrees = temperature_c * (9 / 5) + 32
    Temp_F = "Pico Temperature: " + str(round(fahrenheit_degrees,2)) + " *F"
    utime.sleep(1)
