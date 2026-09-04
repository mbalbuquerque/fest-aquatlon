import os
import requests


MERCADOPAGO_PREFERENCES_URL = (
    "https://api.mercadopago.com/checkout/preferences"
)

SITE_URL = os.getenv(
    "SITE_URL",
    "https://fest-aquatlon.onrender.com",
).rstrip("/")


def criar_preferencia_pagamento(inscricao):
    """
    Cria uma preferência exclusiva do Mercado Pago
    para uma inscrição do FEST AQUATHLON.
    """

    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

    if not access_token:
        raise RuntimeError(
            "MERCADOPAGO_ACCESS_TOKEN não configurado."
        )

    payload = {
        "items": [
            {
                "id": inscricao.numero,
                "title": (
                    f"FEST AQUATHLON 2026 - "
                    f"{inscricao.numero}"
                ),
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(inscricao.valor_total),
            }
        ],

        # Identificador que permitirá ao webhook
        # descobrir exatamente qual inscrição foi paga.
        "external_reference": inscricao.numero,

        "payer": {
            "name": inscricao.nome,
            "email": inscricao.email,
        },

        "back_urls": {
            "success": (
                f"{SITE_URL}/inscricao/sucesso/"
                f"{inscricao.numero}/"
            ),
            "pending": (
                f"{SITE_URL}/pagamento/"
                f"{inscricao.numero}/"
            ),
            "failure": (
                f"{SITE_URL}/pagamento/"
                f"{inscricao.numero}/"
            ),
        },

        "auto_return": "approved",

        "metadata": {
            "inscricao": inscricao.numero,
        },
    }

    response = requests.post(
        MERCADOPAGO_PREFERENCES_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    init_point = data.get("init_point")

    if not init_point:
        raise RuntimeError(
            "Mercado Pago não retornou init_point."
        )

    return init_point