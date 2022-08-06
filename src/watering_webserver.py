from flask import Flask, render_template, request, redirect
import pickle
from threading import Thread
from time import sleep, strftime
import os
import re
#import gpiod
from datetime import datetime

from zeroconf import current_time_millis



app = Flask(__name__)

integer_regex = re.compile("%d")

i = 0
config = {}

relays = {'relay1' : None, 'relay2' : None, 'relay3' : None, 'relay4' : None, 'relay5' : None, 'relay6' : None, 'relay7' : None, 'relay8' : None}
sensors = {'sensor1' : 0, 'sensor2' : 0, 'sensor3' : 0,'sensor4' : 0,'sensor5' : 0,'sensor6' : 0}
pump = None

def ctrl_pump(enable, number):
    relays[number].set_value(1 if enable else 0)

def _get_sensor_val(adc, sensor):
    return int(os.popen("ads_get %s %s 2' %(adc, sensor)").read().replace('\n', ''))

def read_sensors():
    global sensors

    sensors['sensor1'] = _get_sensor_val(1, 0)
    sensors['sensor2'] = _get_sensor_val(1, 1)
    sensors['sensor3'] = _get_sensor_val(1, 2)
    sensors['sensor4'] = _get_sensor_val(1, 3)
    sensors['sensor5'] = _get_sensor_val(2, 0)
    sensors['sensor6'] = _get_sensor_val(2, 1)


def initialize_gpios():
    global pump, relays
    
    c = gpiod.chip("/dev/gpiochip0")
    relays['relay1'] = c.get_line(4)
    relays['relay2'] = c.get_line(17)
    relays['relay3'] = c.get_line(27)
    relays['relay4'] = c.get_line(22)
    relays['relay5'] = c.get_line(10)
    relays['relay6'] = c.get_line(9)
    relays['relay7'] = c.get_line(11)
    relays['relay8'] = c.get_line(18)
    pump = c.get_line(23)
    
    gpiod_config = gpiod.line_request()
    gpiod_config.consumer = "Watering"
    gpiod_config.request_type = gpiod.line_request.DIRECTION_OUTPUT

    for r in relays:
        r.request(gpiod_config)
        r.set_value(0)
        sleep(0.1)
        r.set_value(1)
    pump.request(gpiod_config)
    pump.set_value(0)


def load_config():
    global config
    try:
        config = pickle.load(open( "config.p", "rb" ))
    except:
        # create standard config
        config = {
                    "Watering_Duration" : 5, 
                    "Check_Interval" : 2,
                    "Hysteresis_Threshold" : 1000,
                    "hidden_sensor_thresholds" : {},
                    "Watering_Time" : "20:00",
                    "hidden_relays" : {
                        'relay1' : [], 
                        'relay2' : [],
                        'relay3' : [],
                        'relay4' : [],
                        'relay5' : [],
                        'relay6' : [],
                        'relay7' : [],
                        'relay8' : []
                    }
                    
                }

        for key, value in sensors.items():
            print(key)
            config['hidden_sensor_thresholds'][key] = 10000
        save_config()

def save_config():
    global config
    pickle.dump(config, open( "config.p", "wb" )) 

def get_relays_for_sensor(sensor):
    ret = []
    for k, v in config["hidden_relays"].items():
        for i in v:
            if sensor == i:
                ret.append(k)
    return ret

def water():
    now = datetime.now()
    try:
        watering_date = now.replace(hour=int(config['Watering_Time'].split(":")[0]), minute=int(config['Watering_Time'].split(":")[1]), second=0, microsecond=0)
    except:
        config['Watering_Time'] = "20:00"
        save_config()

    if watering_date < now:
        print("Its time to water the plants")
        for sensor_k, sensor_v in sensors:
            print("Checking: %s %s", (sensor_k, sensor_v))
            if sensor_v < config['hidden_sensor_thresholds'][sensor_k] - config["Hysteresis_Threshold"]:
                print ("Watering for: %s; %s < %s", (sensor_k, sensor_v, config['hidden_sensor_thresholds'][sensor_k] - config["Hysteresis_Threshold"]))
                for relay in get_relays_for_sensor(sensor_k):
                    print("Enable %s" ,(relay))
                    relays[relay].set_value(0)
                    pump.set_value(1)
                    sleep(config['Watering_Duration'] * 60)
                    print("Disable %s" ,(relay))
                    relays[relay].set_value(1)
                    pump.set_value(0)
                    sleep(5) # sleep to prevent overheating from pump
def worker():
    global i, config
    initialize_gpios()
    read_sensors()

    while True:
        i += 1
    
        read_sensors()
        water()
        sleep(config['Check_Interval'] * 60)



@app.route('/get_sensor_values/')
def get_sensor_values():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    
    return dict(
        sensor1=sensors['sensor1'],
        sensor2=sensors['sensor2'],
        sensor3=sensors['sensor3'],
        sensor4=sensors['sensor4'],
        sensor5=sensors['sensor5'],
        sensor6=sensors['sensor6'],
        datetime=current_time
   )

@app.route("/", methods=["GET"])
def index():
    print(config)
    return render_template('index.html', data=i, config=config, sensors=sensors, relays=config['hidden_relays'])

@app.route("/save_sensor", methods=["POST"])
def save_sensor_web():
    global config
    print(request.form)
    sensor = ""
    for key, value in sensors.items():
        try:
            config['hidden_sensor_thresholds'][key] = int(request.form.get(key))
            sensor = key
        except:
            pass
                
    for key, value in config['hidden_relays'].items():
        print (key, value, request.form.get(key))
        try:
            print(request.form.get(key))
            if request.form.get(key) == 'on':
                if sensor not in config['hidden_relays'][key]:
                    config['hidden_relays'][key].append(sensor)
            else:
                if sensor in config['hidden_relays'][key]:
                    config['hidden_relays'][key].remove(sensor)
        except:
            pass

    save_config()
    return redirect('/')  

@app.route("/save_config", methods=["POST"])
def save_config_web():
    global config
    
    for key, value in config.items():
        try:
            config[key] = int(request.form.get(key))
        except:
            pass

    save_config()

    return redirect('/')        

if __name__ == "__main__":
    load_config()

    t = Thread(target=worker)
    t.start()
    
    app.run(debug=True, host="0.0.0.0", port=8000)
        
