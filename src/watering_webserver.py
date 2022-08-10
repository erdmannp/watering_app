from flask import Flask, render_template, request, redirect
import pickle
from threading import Thread, Lock
from time import sleep
from subprocess import run as sp_run
from datetime import datetime
from shlex import split as sh_split


app = Flask(__name__)

i = 0
config = {}
stop_threads = False
relays = {'relay1' : None, 'relay2' : None, 'relay3' : None, 'relay4' : None, 'relay5' : None, 'relay6' : None, 'relay7' : None, 'relay8' : None}
sensors = {'sensor1' : 0, 'sensor2' : 0, 'sensor3' : 0,'sensor4' : 0,'sensor5' : 0,'sensor6' : 0}
pump = None

mutex = Lock()

def ctrl_pump(number):
    global config
    mutex.acquire(blocking=True)

    try:
        r = sp_run(sh_split("gpioset -m time --sec %s 0 %s=0 %s=1" 
            %(config['Watering_Duration'], relays[number], pump)), capture_output=True).stdout
    except OSError as err:
        print("OS error: {0}".format(err))
    mutex.release()

def _get_sensor_val(adc, sensor):
    
    while True :
        try:
            res = int(sp_run(sh_split("ads_get %s %s 2" %(adc, sensor)), capture_output=True).stdout)
            print("Sensor %s %s :%s" %(adc, sensor, res))
            return res
        except:
            sleep(0.1)
            print("Sensor read failed")
            pass

def initialize_gpios():
    global pump, relays
        
    relays['relay1'] = 4
    relays['relay2'] = 17
    relays['relay3'] = 27
    relays['relay4'] = 22
    relays['relay5'] = 10
    relays['relay6'] = 9
    relays['relay7'] = 11
    relays['relay8'] = 18
    pump = 23

    for k, r in relays.items():
        sp_run(sh_split("gpioset -m time --sec 1 %s=0" %(r)), capture_output=True).stdout
    sp_run(sh_split("gpioset -m time --sec 1 %s=1" %(pump)), capture_output=True).stdout

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
                    },
                    "hidden_use_as_level" : ""
                    
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
        print(k, v)
        for i in v:
            print(i)
            if sensor == i:
                ret.append(k)
    return ret

def water():
    global config
    now = datetime.now()

    try:
        watering_date = now.replace(hour=int(config['Watering_Time'].split(":")[0]), minute=int(config['Watering_Time'].split(":")[1]), second=0, microsecond=0)
    except:
        config['Watering_Time'] = "20:00"
        save_config()

    if config['hidden_use_as_level'] != "":
        if sensors[config['hidden_use_as_level']] < config['hidden_sensor_thresholds'][config['hidden_use_as_level']]:
            return # Dont Water anything!

    if watering_date < now:
        print("Its time to water the plants")
        for sensor_k, sensor_v in sensors.items():
            print("Checking: %s %s" %(sensor_k, sensor_v))
            if sensor_v > config['hidden_sensor_thresholds'][sensor_k]:
                print ("Watering for: %s; %s > %s" %(sensor_k, sensor_v, config['hidden_sensor_thresholds'][sensor_k]))
                for relay in get_relays_for_sensor(sensor_k):
                    print("Enable %s" %(relay))
                    ctrl_pump(relay)
                    sleep(5) # sleep to prevent overheating from pump
    else:
        print("Its not the time to water the plants: %s %s" %(watering_date, now))

def worker():
    global i, config
    initialize_gpios()

    while not stop_threads:
        water()
        sleep(config['Check_Interval'] * 60)

def read_sensors():
    global sensors, stop_threads
    while not stop_threads:
        sensors['sensor1'] = _get_sensor_val(1, 0)
        sensors['sensor2'] = _get_sensor_val(1, 1)
        sensors['sensor3'] = _get_sensor_val(1, 2)
        sensors['sensor4'] = _get_sensor_val(1, 3)
        sensors['sensor5'] = _get_sensor_val(2, 0)
        sensors['sensor6'] = _get_sensor_val(2, 1)
        sleep(15)

@app.route('/get_sensor_values/')
def get_sensor_values():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    global sensors

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
    return render_template('index.html', 
        config=config,
        sensors=sensors,
        relays=config['hidden_relays'],
        use_as_level=config['hidden_use_as_level']
    )

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

    try:
        if request.form.get("useAsLevel") == 'on':
            config['hidden_use_as_level'] = sensor
            for key, value in config['hidden_relays'].items():
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
            if key == "Watering_Time":
                config[key] = request.form.get(key)
            else:
                config[key] = int(request.form.get(key))
        except:
            pass

    save_config()

    return redirect('/')        

if __name__ == "__main__":
    load_config()

    worker_thread = Thread(target=worker)
    worker_thread.start()
    
    sensor_thread = Thread(target=read_sensors)
    sensor_thread.start()

    app.run(debug=True, host="0.0.0.0", port=80)
