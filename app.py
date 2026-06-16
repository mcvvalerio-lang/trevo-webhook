from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return "Trevo Online"

@app.route("/webhook/mp", methods=["POST"])
def webhook_mp():
    dados = request.get_json(silent=True)

    print("=== WEBHOOK MP RECEBIDO ===")
    print("Data/hora:", datetime.now().isoformat())
    print("Headers:", dict(request.headers))
    print("JSON:", dados)
    print("===========================")

    return jsonify({
        "status": "ok",
        "mensagem": "Webhook recebido pelo Trevo",
        "dados_recebidos": dados
    }), 200
