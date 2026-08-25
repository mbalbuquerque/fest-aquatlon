import hashlib
import hmac
import os
import requests

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def webhook_mercadopago(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Método não permitido"}, status=405)

    # O Mercado Pago informa o tipo e o ID do pagamento.
    tipo = request.GET.get("type")
    payment_id = request.GET.get("data.id")

    if not payment_id:
        try:
            body = request.json()
            payment_id = body.get("data", {}).get("id")
            tipo = tipo or body.get("type")
        except Exception:
            body = {}

    # Nesta fase queremos apenas eventos de pagamento.
    if tipo and tipo != "payment":
        return JsonResponse({"received": True})

    # Em produção, valide x-signature com a chave secreta
    # do Mercado Pago.
    secret = os.getenv("MERCADOPAGO_WEBHOOK_SECRET")

    if secret:
        x_signature = request.headers.get("x-signature", "")
        x_request_id = request.headers.get("x-request-id", "")

        # O Mercado Pago envia algo como:
        # ts=...,v1=...
        ts = None
        v1 = None

        for item in x_signature.split(","):
            key, _, value = item.partition("=")

            if key == "ts":
                ts = value

            elif key == "v1":
                v1 = value

        if not ts or not v1:
            return JsonResponse(
                {"detail": "Assinatura inválida"},
                status=401,
            )

        manifest = (
            f"id:{payment_id};"
            f"request-id:{x_request_id};"
            f"ts:{ts};"
        )

        generated = hmac.new(
            secret.encode(),
            manifest.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(generated, v1):
            return JsonResponse(
                {"detail": "Assinatura inválida"},
                status=401,
            )

    # Sem Access Token ainda não tentaremos consultar
    # o Mercado Pago.
    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

    if not access_token:
        return JsonResponse({
            "received": True,
            "payment_id": payment_id,
            "detail": "Webhook recebido, mas Access Token ainda não configurado.",
        })

    try:
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            timeout=15,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException:
        return JsonResponse(
            {"detail": "Não foi possível consultar o Mercado Pago."},
            status=502,
        )

    try:
        pagamento = Pagamento.objects.get(
            identificador_transacao=str(payment_id)
        )

    except Pagamento.DoesNotExist:
        return JsonResponse({
            "received": True,
            "payment_id": payment_id,
            "detail": "Pagamento ainda não associado a uma inscrição.",
        })

    status_mp = data.get("status")

    pagamento.metodo = (
        data.get("payment_method_id")
        or data.get("payment_type_id")
        or ""
    )

    pagamento.identificador_transacao = str(payment_id)

    if status_mp == "approved":

        pagamento.status = Pagamento.PAGO
        pagamento.pago_em = timezone.now()

        pagamento.inscricao.status = Inscricao.PAGO
        pagamento.inscricao.save(
            update_fields=[
                "status",
                "atualizado_em",
            ]
        )

    elif status_mp in ["cancelled", "rejected"]:

        pagamento.status = Pagamento.CANCELADO

    elif status_mp == "expired":

        pagamento.status = Pagamento.EXPIRADO

    else:

        pagamento.status = Pagamento.PENDENTE

    pagamento.save()

    return JsonResponse({
        "received": True,
        "payment_id": payment_id,
        "status": status_mp,
    })

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import InscricaoForm
from .models import (
    Inscricao,
    Pagamento,
)
from .pagamentos import obter_link_pagamento


def home(request):
    return render(
        request,
        "inscricoes/home.html",
    )


def nova_inscricao(request):

    vagas = (
        180
        - Inscricao.objects.exclude(
            status=Inscricao.CANCELADO
        ).count()
    )

    if vagas <= 0:
        return render(
            request,
            "registration/encerradas.html",
        )

    form = InscricaoForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST":

        if form.is_valid():

            inscricao = form.save(
                commit=False
            )

            inscricao.save()

            link = obter_link_pagamento(
                inscricao
            )

            Pagamento.objects.create(
                inscricao=inscricao,
                valor=inscricao.valor_total,
                link_pagamento=link,
                status=Pagamento.PENDENTE,
            )

            return redirect(
                "pagamento",
                numero=inscricao.numero,
            )

    return render(
        request,
        "registration/inscricao.html",
        {
            "form": form,
            "vagas": vagas,
        },
    )


def pagamento(request, numero):

    inscricao = get_object_or_404(
        Inscricao,
        numero=numero,
    )

    pagamento = get_object_or_404(
        Pagamento,
        inscricao=inscricao,
    )

    return render(
        request,
        "registration/pagamento.html",
        {
            "inscricao": inscricao,
            "pagamento": pagamento,
        },
    )


def sucesso(request, numero):

    inscricao = get_object_or_404(
        Inscricao,
        numero=numero,
    )

    return render(
        request,
        "registration/sucesso.html",
        {
            "inscricao": inscricao,
        },
    )