from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def home():
    return "Trevo Online"

@app.route("/webhook/mp", methods=["POST"])
def webhook_mp():
    print("Webhook recebido")
    print(request.json)

    return "OK", 200
