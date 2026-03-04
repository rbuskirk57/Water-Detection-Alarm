 # Display Image & text on I2C driven SH1106 OLED display 
from machine import I2C, ADC
from sh1106 import SH1106_I2C
import framebuf
import time
from machine import Pin, I2C
import utime as time
import net_connect
import secrets
from umqttsimple import MQTTClient
import mqtt_params
import utime

s1_status = ""
s2_status = ""
ip_addr = ""
temperature = ""

def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, user=user_t, password=password_t, keepalive=30)
    client.connect()
    print('Connected to %s MQTT Broker'%(mqtt_server))
    return client
# This code is executed once a new message is published
def new_message_callback(topic, msg):
    global s1_status
    global s2_status
    global ip_addr
    global temperature
    topic , msg=topic.decode('ascii') , msg.decode('ascii')
    #print("Topic: "+topic+" | Message: "+msg)
    #print(msg)
    if "S1" in msg:
        s1_status = msg
    elif "S2" in msg:
        s2_status = msg
    elif "192" in msg:
        ip_addr = msg
    elif "Temperature" in msg:
        temperature = msg
    else:
        print("Just a heads-up ... msg in callback didn't match: " + msg)

def reset_pico():
   print('Bailing out with a soft reset...')
   time.sleep(1)
   led.off()
   machine.soft_reset()
   
def row_count(row):
    if row == 45:
        row = 5
    else:
        row += 10
    time.sleep(.1)
    return row

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
    led.on()
else:
    reset_pico()

# the following will set the seconds between 2 keep alive messages
keep_alive=30

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
        # Water Sensor 1
        pub_msg = s1_status
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
        
        # Water Sensor 2
        pub_msg = s2_status
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
        
        pub_lst.append(wheel[count])
        pub_lst.pop(0)
        oled.fill(0)
        
        pub_lst.append(wheel[count])
        pub_lst.pop(0)
        oled.fill(0)
        
        status = temperature[20:28]
        pub_lst.append(status)
        pub_lst.pop(0)

        if count > 4:
            count = 0
        else:
            count += 1

        oled.text(pub_lst[0],5,row[0])
        oled.text(pub_lst[1],5,row[1]) #15 (+10)
        oled.text(pub_lst[2],5,row[2]) #25 (+20)
        oled.text(pub_lst[3],5,row[3])
        oled.text(pub_lst[4],5,row[4])
        oled.show()

		# Scroll
        row[0] = row_count(row[0])
        row[1] = row_count(row[1])
        row[2] = row_count(row[2])
        row[3] = row_count(row[3])
        row[4] = row_count(row[4])

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

