from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "Trevo Online"

@app.route("/webhook/mp", methods=["GET", "POST"])
def webhook_mp():

    print("=== WEBHOOK MP RECEBIDO ===")
    print("Método:", request.method)
    print("Data:", datetime.now().isoformat())

    if request.method == "GET":
        return jsonify({
            "status": "ok",
            "metodo": "GET",
            "mensagem": "Webhook Trevo funcionando"
        })

    dados = request.get_json(silent=True)

    print("JSON:", dados)

    return jsonify({
        "status": "ok",
        "metodo": "POST",
        "dados": dados
    })
