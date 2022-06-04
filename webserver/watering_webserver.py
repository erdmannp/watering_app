from re import I

from cairo import STATUS_INVALID_DSC_COMMENT
from flask import Flask, render_template, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
import pickle

i = 0
config = {}

def load_config():
    global config
    try:
        config = pickle.load(open( "config.p", "rb" ))
    except:
        # create standard config
        config = {"duration" : 5}
        save_config()

def save_config():
    global config
    pickle.dump(config, open( "config.p", "wb" )) 

def sensor():
    global i, config
    i += 1
    print("Test" + str(i))
    print(config)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    print(config)
    return render_template('index.html', data=i, config=config)

@app.route("/save_config", methods=["POST"])
def save_config_web():
    global config
    #config = request.values
    
    print(request.form)
    for key, value in config.items():
        try:
            config[key] = int(request.form.get(key))
        except:
            pass

    save_config()

    return redirect('/')


if __name__ == "__main__":
    load_config()

    sched = BackgroundScheduler(daemon=True)
    sched.add_job(sensor,'interval',seconds=30)
    sched.start()
    app.run(debug=True, host="0.0.0.0")