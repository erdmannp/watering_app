from flask import Flask, render_template, request, redirect
import pickle
from threading import Thread
from time import sleep


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

def worker():
    global i, config

    while True:
        i += 1
        print("Test" + str(i))
        print(config)
        sleep(60)

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

    t = Thread(target=worker)
    t.run()

    app.run(debug=True, host="0.0.0.0")
