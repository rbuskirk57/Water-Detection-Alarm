 # Display Image & text on I2C driven SH1106 OLED display 
from machine import I2C, ADC
from sh1106 import SH1106_I2C
import framebuf
import time
from machine import Pin, I2C
import utime as time
from dht import DHT11, InvalidChecksum
import net_connect
import secrets
from umqttsimple import MQTTClient
import mqtt_params
import utime
#from picozero import pico_led
#import socket

def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, user=user_t, password=password_t, keepalive=30)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client
# This code is executed once a new message is published
def new_message_callback(topic, msg):
    topic , msg=topic.decode('ascii') , msg.decode('ascii')
    #print("Topic: "+topic+" | Message: "+msg)
    #print(msg)
    if "S1" in msg:
        #print("callback: " + msg)
        #clear_file("S1.txt")
        f = open("S1.txt", 'w')
        f.write(msg)
        f.close
    elif "S2" in msg:
        #clear_file("S2.txt")
        f = open("S2.txt", 'w')
        f.write(msg)
        f.close
    elif "192" in msg:
        #clear_file("ip.txt")
        f = open("ip.txt", 'w')
        f.write(msg)
        f.close
    elif "Temperature" in msg:
        #clear_file("temp.txt")
        f = open("temp.txt", 'w')
        f.write(msg)
        f.close
    else:
        print("Just a heads-up ... msg in callback didn't match: " + msg)
    
#     if msg[0:2] == "SD":
#         f = open("sdoor.txt", 'w')
#         f.write(msg)
#         f.close()
#         wrt_sysok("1")
#     elif msg[0:2] == "LD":
#         f = open("ldoor.txt", 'w')
#         f.write(msg)
#         f.close()
#         wrt_sysok("1")
#     elif msg[0:2] == "Te":
#         f = open("temp.txt", 'w')
#         f.write(msg)
#         f.close()
#         wrt_sysok("1")
#     else:
#         print("Just a heads-up ... msg in callback didn't match: " + msg)
#         wrt_sysok("0")

def wrt_sysok(status):
    f = open("sysok.txt", "w")
    f.write(status)
    f.close()

def reset_pico():
   print('Bailing out with a soft reset...')
   time.sleep(1)
   #machine.reset()
   led.off()
   machine.soft_reset()
   
def row_count(row):
    if row == 45:
        row = 5
    else:
        row += 10
    return row

# def clear_file(file):
#     f = open(file, 'w')
#     f.write(" ")
#     f.close
    
# def refresh_screen(pub_lst,row):
#     oled.text(pub_lst[0],5,row[0])
#     oled.text(pub_lst[1],5,row[1]) #15 (+10)
#     oled.text(pub_lst[2],5,row[2]) #25 (+20)
#     oled.text(pub_lst[3],5,row[3])
#     oled.text(pub_lst[4],5,row[4])
#     oled.show()

def read_sensor():
    tc=0
    h=0
    t=0
    try:
        tc  = (sensor.temperature)
    except:
        #time.sleep(1)
        try:
            tc  = (sensor.temperature)
        except:
            #print("temp read error")
            #reset_pico()
            pass
        #pass

    t = tc * (9/5) + 32

    try:
        h = (sensor.humidity)
    except:
        #time.sleep(1)
        try:
            h = (sensor.humidity)
        except:
            #print("Humidity read error")
            pass

    return t,h


WIDTH  = 128                                            # oled display width
HEIGHT = 64                                             # oled display height

i2c = I2C(0)                                            # Init I2C using I2C0 defaults, SCL=Pin(GP9), SDA=Pin(GP8), freq=400000
print("I2C Address      : "+hex(i2c.scan()[0]).upper()) # Display device address
print("I2C Configuration: "+str(i2c))                   # Display I2C config

oled = SH1106_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display
oled.rotate(True)
tc=0
t=0
h=0

count=0
count_h=0
ip = '0'
led = Pin(27, Pin.OUT) #WiFi connected
led.off()


#MQTT Setup
client_id = mqtt_params.client_id
mqtt_server = mqtt_params.mqtt_server
user_t = mqtt_params.user_t
password_t = mqtt_params.password_t
topic_pub = mqtt_params.topic_pub

ip = net_connect.connect(secrets.SSID, secrets.PASSWORD,20)
if ip != "-1":
    #print("connected on: " + ip)
    led.on()
#     connection = open_socket(ip)
else:
    reset_pico()

# the following will set the seconds between 2 keep alive messages
keep_alive=30

#pin = Pin(28, Pin.OUT, Pin.PULL_DOWN)
#pin = Pin(28, Pin.IN)
#sensor = DHT11(pin)

try:
    client = mqtt_connect()
    client.set_callback(new_message_callback)
    client.subscribe(topic_pub.encode('utf-8'))
except OSError as e:
    reset_pico()

last_message=utime.time()

mssg = client.check_msg()

pub_lst = ["0","1","2","3","4"]
row = [5,15,25,35,45]
wheel = ["-","\\","|","/","-","|"]
pid = ""
sensor = ""

while True:
    try:
        f = open("S1.txt")
        pub_msg = f.read()
        f.close()
        pid = "P" + pub_msg[5:6]
        sensor = pub_msg[7:9]
        if "READY" in pub_msg:
            status = "READY"
        elif "NO_SENSOR" in pub_msg:
            status = "NC"
        else:
            status = "Unknown"
        pub_lst.append(pid + ":" + sensor + ":" + status)
        pub_lst.pop(0)
        
        f = open("S2.txt")
        pub_msg = f.read()
        f.close()
        pid = "P" + pub_msg[5:6]
        sensor = pub_msg[7:9]
        if "READY" in pub_msg:
            status = "READY"
        elif "NO_SENSOR" in pub_msg:
            status = "NC"
        else:
            status = "Unknown"
        pub_lst.append(pid + ":" + sensor + ":" + status)
        pub_lst.pop(0)
        
#         f = open("temp.txt")
#         pub_msg = f.read()
#         f.close()
#         pid = "P" + pub_msg[5:6]
#         status = "Temp:" + pub_msg[20:25] + "F"
#         pub_lst.append(pid + ":" + status)
#         pub_lst.pop(0)
#         oled.fill(0)

#         f = open("ip.txt")
#         pub_msg = f.read()
#         f.close()
#         pid = "P" + pub_msg[5:6] + ":"
#         status = pub_msg[19:22]
#         pub_lst.append(pid + status)
        pub_lst.append(wheel[count])
        pub_lst.pop(0)
        oled.fill(0)
        
        pub_lst.append(wheel[count])
        pub_lst.pop(0)
        oled.fill(0)
        
        status = str(t) + "F:" + str(h) + "%"
        pub_lst.append(status)
        pub_lst.pop(0)

        #time.sleep(1)
        pin = Pin(28, Pin.OUT, Pin.PULL_DOWN)
        #pin = Pin(28, Pin.IN)
        sensor = DHT11(pin)

        if count > 4:
            count = 0
            t,h = read_sensor()
        else:
            count += 1

        oled.text(pub_lst[0],5,row[0])
        oled.text(pub_lst[1],5,row[1]) #15 (+10)
        oled.text(pub_lst[2],5,row[2]) #25 (+20)
        oled.text(pub_lst[3],5,row[3])
        oled.text(pub_lst[4],5,row[4])
        oled.show()

		# Scroll
#         row[0] = row_count(row[0])
#         row[1] = row_count(row[1])
#         row[2] = row_count(row[2])
#         row[3] = row_count(row[3])
#         row[4] = row_count(row[4])

        client.check_msg()
        utime.sleep(0.1)
        if (utime.time() - last_message) > keep_alive:
            client.publish(topic_pub, "Keep alive message")
            last_message = utime.time()
        
    except OSError as e:
        print(e)
        reset_pico()
        pass

client.disconnect()