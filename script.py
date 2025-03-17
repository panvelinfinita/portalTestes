from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Carregar variáveis de ambiente
load_dotenv()
vtexKey = os.getenv("vtexKey")
vtexToken = os.getenv("vtexToken")

app = Flask(__name__)

CORS(app)

@app.route("/frete", methods=["POST"])
def calcular_frete():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Nenhum dado enviado"}), 400

        # Pegando os valores recebidos do front-end
        id = data.get("SKU Front", "").strip()
        seller = data.get("Seller (HFZZ)", "").strip()
        cep_destino = data.get("CEP Destino", "").strip()

        # Validação: Se algum campo estiver vazio, retorna erro
        if not id or not seller or not cep_destino:
            return jsonify({"error": "Campos obrigatórios ausentes"}), 400

        # Configuração da requisição para a VTEX
        cURL = "http://panvelprd.vtexcommercestable.com.br/api/checkout/pvt/orderForms/simulation?sc=1"
        header = { 
            "X-VTEX-API-AppKey": vtexKey,
            "X-VTEX-API-AppToken": vtexToken,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        body = {
            "items": [
                {
                    "id": id,
                    "quantity": "1",
                    "seller": seller
                }
            ],
            "postalCode": cep_destino,
            "country": "BRA"
        }

        # Enviando requisição para a VTEX
        response = requests.post(cURL, headers=header, json=body)

        if response.status_code != 200:
            return jsonify({"error": f"Erro na VTEX: {response.status_code}"}), 500

        vtex_data = response.json()
        logistics_info = vtex_data.get("logisticsInfo", [])

        if not logistics_info:
            return jsonify({"error": "logisticsInfo não encontrado"}), 404

        slas = logistics_info[0].get("slas", [])
        if not slas:
            return jsonify({"error": "SLAs não encontrados"}), 404

        shipping_estimate = slas[0].get("shippingEstimate", "Key not found")
        price = slas[0].get("price", "Key not found")

        # Convertendo preço para reais se vier em centavos
        price_in_reais = price / 100 if isinstance(price, int) else price

        resultado = {
            "shippingEstimate": shipping_estimate,
            "price": f"R$ {price_in_reais:.2f}"
        }

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)