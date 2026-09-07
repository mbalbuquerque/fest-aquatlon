from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from urllib.parse import quote

from .models import (
    Inscricao,
    Pagamento,
    Fornecedor,
    ContaPagar,
    ContaReceber,
)

from .pagamentos import criar_preferencia_pagamento

@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):

    list_display = (
    "numero",
    "nome",
    "modalidade",
    "tamanho_camisa",
    "idade",
    "lote",
    "valor_total",
    "status_pagamento",
    "status",
    "militar",
    "criado_em",
)

    list_filter = (
        "modalidade",
        "status",
        "militar",
        "lote",
    )

    search_fields = (
        "numero",
        "nome",
        "email",
        "telefone",
    )

    ordering = (
        "-criado_em",
    )

    readonly_fields = (
        "numero",
        "lote",
        "valor_inscricao",
        "valor_total",
        "botao_whatsapp",
        "criado_em",
        "atualizado_em",
    )

    fieldsets = (
        (
            "Dados do atleta",
            {
                "fields": (
                    "numero",
                    "nome",
                    "telefone",
                    "email",
                    "data_nascimento",
                    "modalidade",
                    "tamanho_camisa",
                )
            },
        ),
        (
            "Condição especial",
            {
                "fields": (
                    "militar",
                    "comprovante_militar",
                    "autorizacao_responsavel",
                )
            },
        ),
        (
            "Financeiro",
            {
                "fields": (
                    "lote",
                    "valor_inscricao",
                    "valor_total",
                    "status",
                    "botao_whatsapp",
                )
            },
        ),
        (
            "Controle",
            {
                "fields": (
                    "criado_em",
                    "atualizado_em",
                )
            },
        ),
    )

    @admin.display(description="Idade")
    def idade(self, obj):
        return obj.idade_no_evento

    @admin.display(description="Pagamento")
    def status_pagamento(self, obj):
        try:
            pagamento = obj.pagamento

        except Pagamento.DoesNotExist:
            try:
                link_pagamento = criar_preferencia_pagamento(obj)

            except Exception:
                link_pagamento = (
                    "https://fest-aquatlon.onrender.com/"
                )

            pagamento = Pagamento.objects.create(
                inscricao=obj,
                valor=obj.valor_total,
                link_pagamento=link_pagamento,
                status=Pagamento.PENDENTE,
            )

        if obj.status == Inscricao.PAGO:
            pagamento.status = Pagamento.PAGO

            if not pagamento.pago_em:
                pagamento.pago_em = timezone.now()

        elif obj.status == Inscricao.CANCELADO:
            pagamento.status = Pagamento.CANCELADO
            pagamento.pago_em = None

        else:
            pagamento.status = Pagamento.PENDENTE
            pagamento.pago_em = None

        pagamento.valor = obj.valor_total
        pagamento.save()

        return pagamento.get_status_display()

    @admin.display(description="Confirmação pelo WhatsApp")
    def botao_whatsapp(self, obj):

        if not obj or not obj.pk:
            return "-"

        # O botão só aparece para inscrições pagas.
        if obj.status != Inscricao.PAGO:
            return mark_safe(
        '<span style="color:#d97706;font-weight:600;">'
        '⚠ Disponível após confirmação do pagamento'
        '</span>'
    )
           

        telefone = "".join(
            filter(str.isdigit, obj.telefone or "")
        )

        if not telefone:
            return "Telefone não informado"

        # Adiciona o código do Brasil quando necessário.
        if not telefone.startswith("55"):
            telefone = f"55{telefone}"

        mensagem = (
            f"Olá, {obj.nome}! 👋\n\n"
            f"Sua inscrição no FEST AQUATHLON 2026 está confirmada! ✅\n\n"
            f"Nome: {obj.nome}\n"
            f"Inscrição: {obj.numero}\n"
            f"Modalidade: {obj.get_modalidade_display()}\n"
            f"Tamanho da camisa: {obj.tamanho_camisa}\n\n"
            f"📅 Data: 20 de dezembro de 2026\n"
            f"📍 Local: Praia do Quartel - Bairro Novo, Olinda/PE\n\n"
            f"Nos vemos na largada! 🏊‍♂️🏃‍♂️"
        )

        url = (
            f"https://wa.me/{telefone}"
            f"?text={quote(mensagem)}"
        )

        return format_html(
            '<a href="{}" '
            'target="_blank" '
            'rel="noopener noreferrer" '
            'style="'
            'display:inline-block;'
            'background:#25D366;'
            'color:#ffffff;'
            'padding:10px 18px;'
            'border-radius:7px;'
            'text-decoration:none;'
            'font-weight:700;'
            'font-size:13px;'
            '">'
            '💬 ENVIAR CONFIRMAÇÃO PELO WHATSAPP'
            '</a>',
            url,
        )
@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):

    list_display = (
        "inscricao",
        "valor",
        "plataforma",
        "status",
        "metodo",
        "criado_em",
        "pago_em",
    )

    list_filter = (
        "status",
        "plataforma",
        "metodo",
    )

    search_fields = (
        "inscricao__numero",
        "inscricao__nome",
        "identificador_transacao",
    )

    readonly_fields = (
        "criado_em",
        "atualizado_em",
    )

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        if obj.status == Pagamento.PAGO:
            obj.pago_em = (
                obj.pago_em
                or timezone.now()
            )

            obj.inscricao.status = Inscricao.PAGO

        elif obj.status == Pagamento.CANCELADO:
            obj.inscricao.status = Inscricao.CANCELADO
            obj.pago_em = None

        else:
            obj.inscricao.status = Inscricao.PENDENTE
            obj.pago_em = None

        obj.inscricao.save()

        super().save_model(
            request,
            obj,
            form,
            change,
        )


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):

    list_display = (
        "nome",
        "documento",
        "telefone",
        "email",
        "ativo",
    )

    list_filter = (
        "ativo",
    )

    search_fields = (
        "nome",
        "documento",
        "email",
        "telefone",
    )


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):

    list_display = (
        "descricao",
        "fornecedor",
        "categoria",
        "valor",
        "vencimento",
        "status",
        "pago_em",
    )

    list_filter = (
        "status",
        "categoria",
        "fornecedor",
    )

    search_fields = (
        "descricao",
        "fornecedor__nome",
    )

    date_hierarchy = "vencimento"

    actions = [
        "marcar_como_pagas",
    ]

    @admin.action(
        description="Marcar selecionadas como pagas"
    )
    def marcar_como_pagas(self, request, queryset):

        hoje = timezone.localdate()
        atualizadas = 0

        for conta in queryset:

            if conta.status != ContaPagar.PAGO:
                conta.status = ContaPagar.PAGO
                conta.pago_em = hoje
                conta.save()

                atualizadas += 1

        self.message_user(
            request,
            f"{atualizadas} conta(s) marcada(s) como paga(s)."
        )


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):

    list_display = (
        "descricao",
        "categoria",
        "valor",
        "vencimento",
        "status",
        "recebido_em",
        "inscricao",
    )

    list_filter = (
        "status",
        "categoria",
    )

    search_fields = (
        "descricao",
        "inscricao__numero",
        "inscricao__nome",
    )

    date_hierarchy = "vencimento"

    actions = [
        "marcar_como_recebidas",
    ]

    @admin.action(
        description="Marcar selecionadas como recebidas"
    )
    def marcar_como_recebidas(
        self,
        request,
        queryset,
    ):

        hoje = timezone.localdate()
        atualizadas = 0

        for conta in queryset:

            if conta.status != ContaReceber.RECEBIDO:
                conta.status = ContaReceber.RECEBIDO
                conta.recebido_em = hoje
                conta.save()

                atualizadas += 1

        self.message_user(
            request,
            f"{atualizadas} conta(s) marcada(s) como recebida(s)."
        )