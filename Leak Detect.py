import secrets
import mqtt_pub_params
import net_connect
import socket
from time import sleep
from picozero import pico_temp_sensor, pico_led, Button
from machine import Pin, PWM
import utime
import machine
from umqttsimple import MQTTClient
import math

def mqtt_serve(door):
    client = mqtt_connect()
    client.publish(mqtt_pub_params.topic_pub, msg=home)
    utime.sleep(3)
        
def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, user=user_t, password=password_t, keepalive=30)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reset_pico():
   print('Bailing out with a machine soft reset...')
   time.sleep(1)
   wifi_led.off()
   machine.soft_reset()
   
client_id = mqtt_pub_params.client_id
mqtt_server = mqtt_pub_params.mqtt_server
user_t = mqtt_pub_params.user_t
password_t = mqtt_pub_params.password_t
        
ip = '0'
wifi_led = Pin(27, Pin.OUT) #WiFi connected

# Sensor 1
alarm_led_1 = Pin(13, Pin.OUT) #Flashing RED = leak detected
Sensor_1_OK_led = Pin(12, Pin.OUT) # Green = Armed; RED = no sensor
#Sensor_1 = Pin(15, Pin.IN, Pin.PULL_UP) # Sensor 1 input
btn1 = Button(15)
Sensor_1_OK = Pin(14, Pin.IN, Pin.PULL_UP) # Sensor detected
# Sensor 2
alarm_led_2 = Pin(18, Pin.OUT) # Flashing RED = leak detected; Solid RED = sensor NC
Sensor_2_OK_led = Pin(19, Pin.OUT) # Green = Armed; RED = no sensor
#Sensor_2 = Pin(16, Pin.IN, Pin.PULL_UP) # Sensor 2 input
btn2 = Button(16)
Sensor_2_OK = Pin(17, Pin.IN, Pin.PULL_UP) # Sensor detected

buzzer = PWM(Pin(21), freq=700)

wifi_led.off()

# Temp Sensor
sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

alarm_led_1.off() # RED ON
Sensor_1_OK_led.on() # GREEN OFF
alarm_led_2.off() # RED ON
Sensor_2_OK_led.on() # GREEN OFF
buzzer.duty_ns(30000)
utime.sleep(1)
buzzer.duty_u16(0) # turn off the buzzer
S1 = "OK"
S2 = "OK"

ip = net_connect.connect(secrets.SSID, secrets.PASSWORD)
if ip != "-1":
    wifi_led.on()
else:
    reset_pico()

while True:
    try:
        client = mqtt_connect()
    except OSError as e:
        reset_pico()

    while True:
        #print("OK: " + str(Sensor_1_OK.value()))
        if Sensor_1_OK.value():
            #Leak detected
            #if not Sensor_1.value():
            if btn1.is_pressed:
                alarm_led_1.toggle()
                Sensor_1_OK_led.on() # GREEN OFF
                #buzzer.duty_u16(32768) # 50% duty cycle
                buzzer.duty_ns(30000)
                S1 = "ALARM_WATER_DETECTED_S1"
            else: # No Leak Sensor Detected
                Sensor_1_OK_led.off() # GREEN
                alarm_led_1.on()
                buzzer.duty_u16(0)
                S1 = "NO_WATER_DETECTED_S1"
        else:
            # No Sensor Detected
            alarm_led_1.off() # RED ON
            Sensor_1_OK_led.on() # GREEN OFF
            buzzer.duty_u16(0) # turn off the buzzer
            S1 = "NO_SENSOR_S1"

        if Sensor_2_OK.value():
            #Leak detected
            #if not Sensor_2.value():
            if btn2.is_pressed:
                alarm_led_2.toggle()
                Sensor_2_OK_led.on() # GREEN OFF
                #buzzer.duty_u16(32768)
                buzzer.duty_ns(30000)
                #print("alarm 2: " + str(Sensor_2.value()))
                S2 = "ALARM_WATER_DETECTED_S2"
            else: # No Leak Sensor Detected
                Sensor_2_OK_led.off() # GREEN
                alarm_led_2.on()
                buzzer.duty_u16(0)
                S2 = "NO_WATER_DETECTED_S2"
        else:
            # No Sensor Detected
            alarm_led_2.off() # RED ON
            Sensor_2_OK_led.on() # GREEN OFF
            S2 = "NO_SENSOR_S2"
                

        reading = sensor_temp.read_u16() * conversion_factor 
        temperature_c = 27 - (reading - 0.706)/0.001721
        fahrenheit_degrees = temperature_c * (9 / 5) + 32
        Temp_F = "Pico Temperature: " + str(round(fahrenheit_degrees,2)) + " *F"
        #utime.sleep(.5)
        
        try:
            client.publish(mqtt_pub_params.topic_pub, msg=S1)
            client.publish(mqtt_pub_params.topic_pub, msg=S2)
            client.publish(mqtt_pub_params.topic_pub, msg=Temp_F)
            utime.sleep(1)
        except:
            print("Client publish failed, executing a machine reset")
            reset_pico()
            pass
    print("client disconnect")
    client.disconnect()
