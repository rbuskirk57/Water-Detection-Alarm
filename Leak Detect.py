import secrets
import mqtt_pub_params
import net_connect
import socket
from picozero import Button
from machine import Pin, PWM
import utime
import machine
from umqttsimple import MQTTClient
import math

def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, user=user_t, password=password_t, keepalive=30)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client

def reset_pico():
   print('Bailing out with a machine soft reset...')
   bummer_tone()
   wifi_led.off()
   machine.soft_reset()
   
def mqtt_lost():
    bummer_tone()
    wifi_led.off()
   
def powerup_tone():
    buzzer.duty_ns(30000)
    buzzer.freq(1000)
    utime.sleep(.1)
    buzzer.freq(1400)
    utime.sleep(.1)
    buzzer.freq(1750)
    utime.sleep(.2)
    buzzer.duty_u16(0)
    
def bummer_tone():
    buzzer.duty_ns(30000)
    buzzer.freq(1300)
    utime.sleep(.5)
    buzzer.freq(950)
    utime.sleep(.5)
    buzzer.duty_u16(0)
    
def wifi_ok_tone():
    buzzer.duty_ns(30000)
    buzzer.freq(1000)
    utime.sleep(.1)
    buzzer.freq(2400)
    utime.sleep(.1)
    buzzer.duty_u16(0)
    
def wifi_connect(max_count):
    ip = net_connect.connect(secrets.SSID, secrets.PASSWORD, max_count)
    if ip != "-1":
        wifi_led.on()
        ip_ok = 1
        wifi_ok_tone()
    return ip_ok
   
client_id = mqtt_pub_params.client_id
mqtt_server = mqtt_pub_params.mqtt_server
user_t = mqtt_pub_params.user_t
password_t = mqtt_pub_params.password_t
        
ip = '0'
wifi_led = Pin(27, Pin.OUT) #WiFi connected

# Sensor 1
alarm_led_1 = Pin(13, Pin.OUT) #Flashing RED = leak detected
Sensor_1_OK_led = Pin(12, Pin.OUT) # Green = Armed; RED = no sensor
btn1 = Button(15)
Sensor_1_OK = Pin(14, Pin.IN, Pin.PULL_UP) # Sensor detected
# Sensor 2
alarm_led_2 = Pin(18, Pin.OUT) # Flashing RED = leak detected; Solid RED = sensor NC
Sensor_2_OK_led = Pin(19, Pin.OUT) # Green = Armed; RED = no sensor
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
powerup_tone()
S1 = "OK"
S2 = "OK"
ip_ok = 0
retry_count = 0
retry_delay = 20

ip_ok = wifi_connect(20)

while True:
    print("ip_ok: " + str(ip_ok))
    if ip_ok:
        try:
            client = mqtt_connect()
        except OSError as e:
            reset_pico()

    while True:
        if Sensor_1_OK.value():
            #Leak detected
            if btn1.is_pressed:
                alarm_led_1.toggle()
                Sensor_1_OK_led.on() # GREEN OFF
                #buzzer.duty_u16(32768) # 50% duty cycle
                buzzer.freq(1000)
                buzzer.duty_ns(30000)
                S1 = "ALARM_WATER_DETECTED_S1"
            else: # No Leak Sensor Detected
                Sensor_1_OK_led.off() # GREEN
                alarm_led_1.on()
                buzzer.duty_u16(0)
                S1 = "S1_READY"
        else:
            # No Sensor Detected
            alarm_led_1.off() # RED ON
            Sensor_1_OK_led.on() # GREEN OFF
            buzzer.duty_u16(0) # turn off the buzzer
            S1 = "S1_NO_SENSOR"

        if Sensor_2_OK.value():
            #Leak detected
            if btn2.is_pressed:
                alarm_led_2.toggle()
                Sensor_2_OK_led.on() # GREEN OFF
                #buzzer.duty_u16(32768)
                buzzer.freq(1000)
                buzzer.duty_ns(30000)
                S2 = "ALARM_WATER_DETECTED_S2"
            else: # No Leak Sensor Detected
                Sensor_2_OK_led.off() # GREEN
                alarm_led_2.on()
                buzzer.duty_u16(0)
                S2 = "S2_READY"
        else:
            # No Sensor Detected
            alarm_led_2.off() # RED ON
            Sensor_2_OK_led.on() # GREEN OFF
            S2 = "S2_NO_SENSOR"
                

        utime.sleep(1)
        reading = sensor_temp.read_u16() * conversion_factor 
        temperature_c = 27 - (reading - 0.706)/0.001721
        fahrenheit_degrees = temperature_c * (9 / 5) + 32
        Temp_F = "Pico Temperature: " + str(round(fahrenheit_degrees,2)) + " *F"
        
        if ip_ok:
            try:
                client.publish(mqtt_pub_params.topic_pub, msg=S1)
                client.publish(mqtt_pub_params.topic_pub, msg=S2)
                client.publish(mqtt_pub_params.topic_pub, msg=Temp_F)
            except:
                print("Client publish failed!")
                mqtt_lost()
                ip_ok = 0
                pass
        else:
            wifi_led.toggle()
            if retry_count >= retry_delay:
                ip_ok = wifi_connect(10)
                if ip_ok:
                    try:
                        client = mqtt_connect()
                    except:
                        print("Retry mqtt_connect failed")
                    retry_count = 0
            else:
                retry_count += 1
            
    print("client disconnect")
    client.disconnect()
