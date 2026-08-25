LINK_MP_PROMOCIONAL = (
    "https://www.mercadopago.com.br/checkout/v1/payment/"
    "redirect/dbf6e08c-c02f-4748-8490-5dab75f0c8f4/"
    "payment-option-form/?source=link&router-request-id="
    "91b8fe7f-4b03-4864-84c7-1d492186d5e4&preference-id="
    "2266606201-a923b168-23d1-41bf-90f5-d6512843d24b"
    "&p=15b63067ae3a3b3ce257d70988192b06"
)

LINK_MP_60_MENOR = (
    "https://www.mercadopago.com.br/checkout/v1/payment/"
    "redirect/?source=link&router-request-id="
    "22d044ed-0287-4773-81e3-a2d53949cc1c&preference-id="
    "2266606201-788f2cc1-da2d-48e2-96cc-fe383a08c512"
)

LINK_MP_MILITAR = (
    "https://www.mercadopago.com.br/checkout/v1/payment/"
    "redirect/?source=link&router-request-id="
    "fe5d5c8b-e30a-4d0f-807b-f4a5cd6b1143&preference-id="
    "2266606201-8797c72e-8ef1-4841-be0c-c7bfb912e406"
)

LINK_MP_17_59 = (
    "https://www.mercadopago.com.br/checkout/v1/payment/"
    "redirect/?source=link&router-request-id="
    "f6d131e2-1dee-404b-aa36-dbcf961f1c8c&preference-id="
    "2266606201-6f5df32d-f9a4-4c2d-a62d-e755bad46223"
)


def obter_link_pagamento(inscricao):

    data = inscricao.criado_em.date()
    idade = inscricao.idade_no_evento

    # Lote promocional
    if data <= __import__("datetime").date(2026, 9, 20):
        return LINK_MP_PROMOCIONAL

    # Segundo lote
    if inscricao.militar:
        return LINK_MP_MILITAR

    if idade < 17 or idade >= 60:
        return LINK_MP_60_MENOR

    return LINK_MP_17_59