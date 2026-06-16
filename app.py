import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
import uuid

@app.route("/criar-order-pix-teste")
def criar_order_pix_teste():
    url = "https://api.mercadopago.com/v1/orders"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }

    payload = {
        "type": "online",
        "external_reference": "C1543_P87",
        "total_amount": "3.00",
        "description": "Bolão Trevo - Concurso 1543",
        "payer": {
            "email": "teste@testuser.com"
        },
        "transactions": {
            "payments": [
                {
                    "amount": "3.00",
                    "payment_method": {
                        "id": "pix",
                        "type": "bank_transfer"
                    }
                }
            ]
        }
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)

    print("=== CRIAR ORDER PIX TESTE ===")
    print("HTTP:", resp.status_code)
    print("Resposta:", resp.text)

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
