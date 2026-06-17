import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime
from pathlib import Path
import json
import time

app = Flask(__name__)
BASE_EVENTOS = Path("eventos_mp")
DIR_PENDENTES = BASE_EVENTOS / "pendentes"
DIR_PROCESSADOS = BASE_EVENTOS / "processados"
DIR_ERROS = BASE_EVENTOS / "erros"

for pasta in [DIR_PENDENTES, DIR_PROCESSADOS, DIR_ERROS]:
    pasta.mkdir(parents=True, exist_ok=True)
    

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
import uuid

def gravar_evento_pendente(evento):
    payment_id = evento.get("payment_id") or "sem_payment_id"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    nome_tmp = f"mp_{timestamp}_{payment_id}.tmp"
    nome_json = f"mp_{timestamp}_{payment_id}.json"

    caminho_tmp = DIR_PENDENTES / nome_tmp
    caminho_json = DIR_PENDENTES / nome_json

    with open(caminho_tmp, "w", encoding="utf-8") as arquivo:
        json.dump(evento, arquivo, ensure_ascii=False, indent=2)

    caminho_tmp.rename(caminho_json)

    return nome_json
    
@app.route("/consultar/<payment_id>")
def consultar(payment_id):
    return jsonify(consultar_pagamento(payment_id))
    
@app.route("/criar-pix-real-teste")
def criar_pix_real_teste():

    url = "https://api.mercadopago.com/v1/orders"

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": str(uuid.uuid4())
    }

    payload = {
        "type": "online",
        "external_reference": "TESTE_REAL_001",
        "total_amount": "1.50",
        "description": "Teste Real Mercado Pago R$ 1,00",
        "payer": {
            "email": "mcv.valerio@gmail.com"
        },
        "transactions": {
            "payments": [
                {
                    "amount": "1.50",
                    "payment_method": {
                        "id": "pix",
                        "type": "bank_transfer"
                    }
                }
            ]
        }
    }

    resp = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=20
    )

    resp_json = resp.json()

    print("=== PIX REAL TESTE ===")
    print("HTTP:", resp.status_code)
    print("Resposta:", resp_json)

    try:
        pagamento = resp_json["transactions"]["payments"][0]
        metodo = pagamento["payment_method"]

        return jsonify({
            "status": resp_json.get("status"),
            "order_id": resp_json.get("id"),
            "external_reference": resp_json.get("external_reference"),
            "payment_id": pagamento.get("id"),
            "ticket_url": metodo.get("ticket_url"),
            "qr_code": metodo.get("qr_code")
        })

    except Exception:
        return jsonify(resp_json), resp.status_code        
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
            "email": "test_payer_154387@testuser.com"
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

    resp = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=20
    )

    resp_json = resp.json()

    print("=== CRIAR ORDER PIX TESTE ===")
    print("HTTP:", resp.status_code)
    print("Resposta:", resp_json)

    try:
        pagamento = resp_json["transactions"]["payments"][0]
        metodo = pagamento["payment_method"]

        return jsonify({
            "status": resp_json.get("status"),
            "order_id": resp_json.get("id"),
            "external_reference": resp_json.get("external_reference"),
            "payment_id": pagamento.get("id"),
            "ticket_url": metodo.get("ticket_url"),
            "qr_code": metodo.get("qr_code")
        })

    except Exception:
        return jsonify(resp_json), resp.status_code
        
@app.route("/")
def home():
    return "Trevo Online"

@app.route("/webhook/mp", methods=["GET", "POST"])
def webhook_mp():
    if request.method == "GET":
        return jsonify({
            "status": "ok",
            "mensagem": "Webhook Trevo funcionando"
        })

    dados = request.get_json(silent=True) or {}
    args = request.args.to_dict()

    print("=== WEBHOOK MP RECEBIDO ===")
    print("ARGS:", args)
    print("JSON:", dados)

    payment_id = (
        dados.get("data", {}).get("id")
        or dados.get("id")
        or args.get("data.id")
        or args.get("id")
    )

    if not payment_id:
        return jsonify({
            "status": "ignorado",
            "motivo": "payment_id não encontrado"
        }), 200

    consulta = consultar_pagamento(payment_id)

    if consulta["http_status"] != 200:
        evento_erro = {
            "tipo": "ERRO_CONSULTA_MP",
            "payment_id": payment_id,
            "http_status": consulta["http_status"],
            "resposta": consulta["resposta"],
            "webhook_json": dados,
            "webhook_args": args,
            "criado_em": datetime.now().isoformat(timespec="seconds")
        }

        gravar_evento_pendente(evento_erro)

        return jsonify({
            "status": "erro_consulta",
            "payment_id": payment_id
        }), 200

    pagamento = consulta["resposta"]

    evento = {
        "tipo": "PAGAMENTO_MP",
        "payment_id": str(pagamento.get("id")),
        "status": pagamento.get("status"),
        "status_detail": pagamento.get("status_detail"),
        "external_reference": pagamento.get("external_reference"),
        "valor": pagamento.get("transaction_amount"),
        "valor_liquido": pagamento.get("transaction_details", {}).get("net_received_amount"),
        "order_id": pagamento.get("order", {}).get("id"),
        "date_approved": pagamento.get("date_approved"),
        "date_created": pagamento.get("date_created"),
        "webhook_json": dados,
        "webhook_args": args,
        "criado_em": datetime.now().isoformat(timespec="seconds")
    }

    nome_arquivo = gravar_evento_pendente(evento)

    return jsonify({
        "status": "evento_gravado",
        "arquivo": nome_arquivo,
        "payment_id": payment_id
    }), 200
    
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
@app.route("/eventos/pagamento", methods=["GET"])
def listar_eventos_pagamento():
    arquivos = sorted(DIR_PENDENTES.glob("*.json"))

    return jsonify({
        "total": len(arquivos),
        "arquivos": [arquivo.name for arquivo in arquivos]
    })


@app.route("/eventos/pagamento/<nome_arquivo>", methods=["GET"])
def obter_evento_pagamento(nome_arquivo):
    caminho = DIR_PENDENTES / nome_arquivo

    if not caminho.exists():
        return jsonify({
            "ok": False,
            "mensagem": "Evento não encontrado"
        }), 404

    with open(caminho, "r", encoding="utf-8") as arquivo:
        evento = json.load(arquivo)

    return jsonify({
        "ok": True,
        "arquivo": nome_arquivo,
        "evento": evento
    })


@app.route("/eventos/pagamento/<nome_arquivo>/confirmar", methods=["POST"])
def confirmar_evento_pagamento(nome_arquivo):
    origem = DIR_PENDENTES / nome_arquivo
    destino = DIR_PROCESSADOS / nome_arquivo

    if not origem.exists():
        return jsonify({
            "ok": False,
            "mensagem": "Evento não encontrado"
        }), 404

    origem.rename(destino)

    return jsonify({
        "ok": True,
        "mensagem": "Evento confirmado e movido para processados",
        "arquivo": nome_arquivo
    })
