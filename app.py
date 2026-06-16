import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
import uuid

@app.route("/criar-pix-teste")
def criar_pix_teste():
    url = "https://api.mercadopago.com/v1/payments"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }

    payload = {
        "transaction_amount": 3.00,
        "description": "Bolão Trevo - Concurso 1543",
        "payment_method_id": "pix",
        "external_reference": "C1543_P87",
        "notification_url": "https://trevo-webhook.onrender.com/webhook/mp",
        "payer": {
            "email": "mcv.valerio@gmail.com"
        }
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    return jsonify(resp.json()), resp.status_code
    
@app.route("/")
def home():
    return "Trevo Online"

@app.route("/webhook/mp", methods=["GET", "POST"])
def webhook_mp():
    if request.method == "GET":
        return jsonify({"status": "ok", "mensagem": "Webhook Trevo funcionando"})

    evento = request.get_json(silent=True) or {}
    print("=== WEBHOOK MP RECEBIDO ===")
    print("Data:", datetime.now().isoformat())
    print("Evento:", evento)

    tipo = evento.get("type")
    payment_id = (evento.get("data") or {}).get("id")

    if tipo == "payment" and payment_id:
        detalhes = consultar_pagamento(payment_id)
        print("Detalhes do pagamento:", detalhes)

        return jsonify({
            "status": "ok",
            "payment_id": payment_id,
            "detalhes": detalhes
        }), 200

    return jsonify({"status": "ignorado", "evento": evento}), 200


def consultar_pagamento(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
    }

    resp = requests.get(url, headers=headers, timeout=15)

    return {
        "http_status": resp.status_code,
        "resposta": resp.json() if resp.content else None
    }
