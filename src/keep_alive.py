from flask import Flask, make_response, request
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    response = make_response("<h1>Success</h1>")
    response.status_code = 200
    return response

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
