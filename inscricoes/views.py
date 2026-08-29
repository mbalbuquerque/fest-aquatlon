from datetime import datetime
import hashlib
import hmac
import json
import os

import requests

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.http import JsonResponse, request
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import InscricaoForm
from .models import (
    Inscricao,
    Pagamento,
    ContaPagar,
    ContaReceber,
)
from .pagamentos import obter_link_pagamento


def home(request):
    return render(
        request,
        "inscricoes/home.html",
    )


def nova_inscricao(request):
    """
    Cadastro público do atleta.
    Cria a inscrição e, em seguida, o respectivo pagamento.
    """

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

    if request.method == "POST" and form.is_valid():

        inscricao = form.save(
            commit=False
        )
        inscricao.save()

        # Cria o pagamento da inscrição.
        pagamento, _ = Pagamento.objects.get_or_create(
            inscricao=inscricao,
            defaults={
                "valor": inscricao.valor_total,
                "link_pagamento": obter_link_pagamento(
                    inscricao
                ),
                "status": Pagamento.PENDENTE,
            },
        )

        # Garante que o valor/link acompanhem a inscrição.
        pagamento.valor = inscricao.valor_total
        pagamento.link_pagamento = obter_link_pagamento(
            inscricao
        )
        pagamento.save(
            update_fields=[
                "valor",
                "link_pagamento",
                "atualizado_em",
            ]
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

    pagamento, _ = Pagamento.objects.get_or_create(
        inscricao=inscricao,
        defaults={
            "valor": inscricao.valor_total,
            "link_pagamento": obter_link_pagamento(
                inscricao
            ),
            "status": Pagamento.PENDENTE,
        },
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


@staff_member_required
def dashboard(request):
    """
    Dashboard principal do evento.
    Consolida inscrições, pagamentos, receitas extras,
    contas a pagar e indicadores.
    """

    hoje = timezone.localdate()

    # =====================================================
    # INSCRIÇÕES
    # =====================================================

    inscritos = (
        Inscricao.objects
        .exclude(
            status=Inscricao.CANCELADO
        )
    )

    total_inscricoes = inscritos.count()

    total_canceladas = (
        Inscricao.objects
        .filter(
            status=Inscricao.CANCELADO
        )
        .count()
    )

    # =====================================================
    # PAGAMENTOS DAS INSCRIÇÕES
    # =====================================================

    pagamentos_pagos = (
        Pagamento.objects
        .filter(
            status=Pagamento.PAGO
        )
    )

    pagamentos_pendentes = (
        Pagamento.objects
        .filter(
            status=Pagamento.PENDENTE
        )
    )

    total_pagas = pagamentos_pagos.count()
    total_pendentes = pagamentos_pendentes.count()

    recebido_pagamentos = (
        pagamentos_pagos
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    a_receber_pagamentos = (
        pagamentos_pendentes
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    # =====================================================
    # CONTAS A RECEBER / RECEITAS EXTRAS
    # =====================================================

    receitas_recebidas = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.RECEBIDO
        )
    )

    receitas_pendentes = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.PENDENTE
        )
    )

    receitas_vencidas = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.PENDENTE,
            vencimento__lt=hoje,
        )
    )

    recebido_extras = (
        receitas_recebidas
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    a_receber_extras = (
        receitas_pendentes
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    receitas_extras_vencidas = (
        receitas_vencidas
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL DE RECEITAS
    # =====================================================

    recebido = (
        recebido_pagamentos
        + recebido_extras
    )

    a_receber = (
        a_receber_pagamentos
        + a_receber_extras
    )

    receita_prevista = (
        recebido
        + a_receber
    )

    # =====================================================
    # CONTAS A PAGAR
    # =====================================================

    despesas_pagas = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PAGO
        )
    )

    despesas_pendentes = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PENDENTE
        )
    )

    despesas_vencidas = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PENDENTE,
            vencimento__lt=hoje,
        )
    )

    contas_pagas = (
        despesas_pagas
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    contas_pendentes = (
        despesas_pendentes
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    contas_vencidas = (
        despesas_vencidas
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_despesas = (
        contas_pagas
        + contas_pendentes
    )

    # =====================================================
    # RESULTADO FINANCEIRO
    # =====================================================

    saldo_atual = (
        recebido
        - contas_pagas
    )

    resultado_previsto = (
        receita_prevista
        - total_despesas
    )

    # =====================================================
    # VAGAS
    # =====================================================

    vagas_totais = 180

    vagas_restantes = max(
        vagas_totais - total_inscricoes,
        0,
    )

    ocupacao = (
        total_inscricoes
        / vagas_totais
        * 100
        if vagas_totais
        else 0
    )

    # =====================================================
    # MODALIDADES
    # =====================================================

    mini_sprint = (
        inscritos
        .filter(
            modalidade=Inscricao.MINI
        )
        .count()
    )

    sprint = (
        inscritos
        .filter(
            modalidade=Inscricao.SPRINT
        )
        .count()
    )

    # =====================================================
    # PERFIL DOS PARTICIPANTES
    # =====================================================

    menor_17 = 0
    idade_17_59 = 0
    idade_60_mais = 0
    total_militares = 0

    for atleta in inscritos.iterator():

        idade = atleta.idade_no_evento

        if idade is None:
            continue

        if idade < 17:
            menor_17 += 1
        elif idade <= 59:
            idade_17_59 += 1
        else:
            idade_60_mais += 1

        if atleta.militar:
            total_militares += 1

    percentual_pagamentos = (
        total_pagas
        / total_inscricoes
        * 100
        if total_inscricoes
        else 0
    )

    # =====================================================
    # ÚLTIMOS LANÇAMENTOS
    # =====================================================

    ultimas_contas_pagar = (
        ContaPagar.objects
        .select_related("fornecedor")
        .order_by("-criado_em")[:5]
    )

    ultimas_contas_receber = (
        ContaReceber.objects
        .order_by("-criado_em")[:5]
    )

    # =====================================================
    # CONTEXTO
    # =====================================================

    contexto = {
        "total_inscricoes": total_inscricoes,
        "total_canceladas": total_canceladas,
        "total_pagas": total_pagas,
        "total_pendentes": total_pendentes,
        "recebido": recebido,
        "a_receber": a_receber,
        "receita_prevista": receita_prevista,
        "receitas_extras_vencidas": receitas_extras_vencidas,
        "contas_pagas": contas_pagas,
        "contas_pendentes": contas_pendentes,
        "contas_vencidas": contas_vencidas,
        "total_despesas": total_despesas,
        "saldo_atual": saldo_atual,
        "resultado_previsto": resultado_previsto,
        "vagas_totais": vagas_totais,
        "vagas_restantes": vagas_restantes,
        "ocupacao": round(ocupacao, 1),
        "mini_sprint": mini_sprint,
        "sprint": sprint,
        "menor_17": menor_17,
        "idade_17_59": idade_17_59,
        "idade_60_mais": idade_60_mais,
        "total_militares": total_militares,
        "percentual_pagamentos": round(
            percentual_pagamentos,
            1,
        ),
        "ultimas_contas_pagar": ultimas_contas_pagar,
        "ultimas_contas_receber": ultimas_contas_receber,
    }

    return render(
        request,
        "inscricoes/dashboard.html",
        contexto,
    )


@staff_member_required
def extrato_financeiro(request):
    """
    Extrato financeiro por período.
    Mostra apenas valores efetivamente recebidos/pagos.
    """

    hoje = timezone.localdate()

    inicio_str = request.GET.get("inicio")
    fim_str = request.GET.get("fim")

    if inicio_str:
        try:
            inicio = datetime.strptime(
                inicio_str,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            inicio = hoje.replace(day=1)
    else:
        inicio = hoje.replace(day=1)

    if fim_str:
        try:
            fim = datetime.strptime(
                fim_str,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            fim = hoje
    else:
        fim = hoje

    # Evita período invertido.
    if inicio > fim:
        inicio, fim = fim, inicio
        
        
@staff_member_required
def relatorios(request):
    """
    Relatório geral do evento.
    Consolida inscrições, pagamentos,
    contas a receber e contas a pagar.
    """

    hoje = timezone.localdate()

    # =====================================================
    # INSCRIÇÕES
    # =====================================================

    total_inscricoes = (
        Inscricao.objects
        .exclude(
            status=Inscricao.CANCELADO
        )
        .count()
    )

    # =====================================================
    # PAGAMENTOS DAS INSCRIÇÕES
    # =====================================================

    total_pagas = (
        Pagamento.objects
        .filter(
            status=Pagamento.PAGO
        )
        .count()
    )

    total_pendentes = (
        Pagamento.objects
        .filter(
            status=Pagamento.PENDENTE
        )
        .count()
    )

    total_recebido_inscricoes = (
        Pagamento.objects
        .filter(
            status=Pagamento.PAGO
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_a_receber_inscricoes = (
        Pagamento.objects
        .filter(
            status=Pagamento.PENDENTE
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    # =====================================================
    # CONTAS A RECEBER
    # =====================================================

    total_recebido_extras = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.RECEBIDO
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_a_receber_extras = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.PENDENTE
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_receitas_extras_vencidas = (
        ContaReceber.objects
        .filter(
            status=ContaReceber.PENDENTE,
            vencimento__lt=hoje
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    # =====================================================
    # TOTAL DE RECEITAS
    # =====================================================

    total_recebido = (
        total_recebido_inscricoes
        + total_recebido_extras
    )

    total_a_receber = (
        total_a_receber_inscricoes
        + total_a_receber_extras
    )

    receita_prevista = (
        total_recebido
        + total_a_receber
    )

    # =====================================================
    # CONTAS A PAGAR
    # =====================================================

    total_contas_pagas = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PAGO
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_contas_pendentes = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PENDENTE
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    total_contas_vencidas = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.VENCIDO
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    # Também considera pendentes já vencidas,
    # mesmo que o status ainda esteja PENDENTE.
    total_pendentes_vencidas = (
        ContaPagar.objects
        .filter(
            status=ContaPagar.PENDENTE,
            vencimento__lt=hoje
        )
        .aggregate(
            total=Sum("valor")
        )["total"]
        or 0
    )

    despesas_previstas = (
        total_contas_pagas
        + total_contas_pendentes
    )

    # =====================================================
    # RESULTADO
    # =====================================================

    saldo_atual = (
        total_recebido
        - total_contas_pagas
    )

    resultado_previsto = (
        receita_prevista
        - despesas_previstas
    )

    # =====================================================
    # MODALIDADES
    # =====================================================

    mini_sprint = (
        Inscricao.objects
        .filter(
            modalidade=Inscricao.MINI
        )
        .exclude(
            status=Inscricao.CANCELADO
        )
        .count()
    )

    sprint = (
        Inscricao.objects
        .filter(
            modalidade=Inscricao.SPRINT
        )
        .exclude(
            status=Inscricao.CANCELADO
        )
        .count()
    )

    # =====================================================
    # PERCENTUAL DE PAGAMENTOS
    # =====================================================

    percentual_pagamentos = (
        total_pagas
        / total_inscricoes
        * 100
        if total_inscricoes
        else 0
    )

    # =====================================================
    # CONTEXTO
    # =====================================================

    contexto = {
        "hoje": hoje,

        "total_inscricoes":
            total_inscricoes,

        "total_pagas":
            total_pagas,

        "total_pendentes":
            total_pendentes,

        "total_recebido":
            total_recebido,

        "total_a_receber":
            total_a_receber,

        "receita_prevista":
            receita_prevista,

        "total_recebido_inscricoes":
            total_recebido_inscricoes,

        "total_recebido_extras":
            total_recebido_extras,

        "total_a_receber_inscricoes":
            total_a_receber_inscricoes,

        "total_a_receber_extras":
            total_a_receber_extras,

        "total_receitas_extras_vencidas":
            total_receitas_extras_vencidas,

        "total_contas_pagas":
            total_contas_pagas,

        "total_contas_pendentes":
            total_contas_pendentes,

        "total_contas_vencidas":
            total_contas_vencidas,

        "total_pendentes_vencidas":
            total_pendentes_vencidas,

        "despesas_previstas":
            despesas_previstas,

        "saldo_atual":
            saldo_atual,

        "resultado_previsto":
            resultado_previsto,

        "mini_sprint":
            mini_sprint,

        "sprint":
            sprint,

        "percentual_pagamentos":
            round(
                percentual_pagamentos,
                1
            ),
    }

    return render(
        request,
        "inscricoes/relatorio.html",
        contexto,
    )

@csrf_exempt
def webhook_mercadopago(request):
    """
    Recebe notificações do Mercado Pago.

    IMPORTANTE:
    Com os links de pagamento estáticos usados atualmente,
    o webhook só consegue atualizar automaticamente uma inscrição
    quando o ID da transação já estiver associado ao pagamento.

    Para confirmação automática por atleta, o ideal é migrar para
    preferências únicas por inscrição ou outra estratégia que gere
    uma identificação individual.
    """

    if request.method != "POST":
        return JsonResponse(
            {
                "detail": "Método não permitido",
            },
            status=405,
        )

    try:
        body = json.loads(
            request.body.decode("utf-8")
            or "{}"
        )
    except (json.JSONDecodeError, UnicodeDecodeError):
        body = {}

    tipo = (
        request.GET.get("type")
        or body.get("type")
    )

    payment_id = (
        request.GET.get("data.id")
        or body.get("data", {}).get("id")
    )

    # Ignora eventos que não sejam de pagamento.
    if tipo and tipo != "payment":
        return JsonResponse(
            {
                "received": True,
            }
        )

    if not payment_id:
        return JsonResponse(
            {
                "received": True,
                "detail": "Notificação sem payment_id.",
            }
        )

    # =====================================================
    # VALIDAÇÃO DA ASSINATURA
    # =====================================================

    secret = os.getenv(
        "MERCADOPAGO_WEBHOOK_SECRET"
    )

    if secret:

        x_signature = request.headers.get(
            "x-signature",
            "",
        )

        x_request_id = request.headers.get(
            "x-request-id",
            "",
        )

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
                {
                    "detail": "Assinatura inválida.",
                },
                status=401,
            )

        manifest = (
            f"id:{payment_id};"
            f"request-id:{x_request_id};"
            f"ts:{ts};"
        )

        generated = hmac.new(
            secret.encode("utf-8"),
            manifest.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            generated,
            v1,
        ):
            return JsonResponse(
                {
                    "detail": "Assinatura inválida.",
                },
                status=401,
            )

    # =====================================================
    # ACCESS TOKEN
    # =====================================================

    access_token = os.getenv(
        "MERCADOPAGO_ACCESS_TOKEN"
    )

    if not access_token:
        return JsonResponse(
            {
                "received": True,
                "payment_id": payment_id,
                "detail":
                    "Access Token não configurado.",
            }
        )

    # =====================================================
    # CONSULTA AO MERCADO PAGO
    # =====================================================

    try:

        response = requests.get(
            (
                "https://api.mercadopago.com/"
                f"v1/payments/{payment_id}"
            ),
            headers={
                "Authorization":
                    f"Bearer {access_token}",
            },
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException:

        return JsonResponse(
            {
                "detail":
                    "Não foi possível consultar o Mercado Pago.",
            },
            status=502,
        )

    status_mp = data.get("status")

    # =====================================================
    # LOCALIZA PAGAMENTO
    # =====================================================

    try:

        pagamento = (
            Pagamento.objects
            .select_related("inscricao")
            .get(
                identificador_transacao=
                    str(payment_id)
            )
        )

    except Pagamento.DoesNotExist:

        return JsonResponse(
            {
                "received": True,
                "payment_id": payment_id,
                "status": status_mp,
                "detail":
                    "Pagamento ainda não associado a uma inscrição.",
            }
        )

    # =====================================================
    # ATUALIZA DADOS
    # =====================================================

    pagamento.metodo = (
        data.get("payment_method_id")
        or data.get("payment_type_id")
        or ""
    )

    pagamento.identificador_transacao = (
        str(payment_id)
    )

    if status_mp == "approved":

        pagamento.status = Pagamento.PAGO

        if not pagamento.pago_em:
            pagamento.pago_em = timezone.now()

        pagamento.inscricao.status = (
            Inscricao.PAGO
        )

        pagamento.inscricao.save(
            update_fields=[
                "status",
                "atualizado_em",
            ]
        )

    elif status_mp in (
        "cancelled",
        "rejected",
    ):

        pagamento.status = (
            Pagamento.CANCELADO
        )

    elif status_mp == "expired":

        pagamento.status = (
            Pagamento.EXPIRADO
        )

    else:

        pagamento.status = (
            Pagamento.PENDENTE
        )

    pagamento.save()

    return JsonResponse(
        {
            "received": True,
            "payment_id": payment_id,
            "status": status_mp,
        }
    )
