from django.contrib import admin
from django.utils import timezone

from .models import (
    Inscricao,
    Pagamento,
    Fornecedor,
    ContaPagar,
    ContaReceber,
)

from .pagamentos import (
    obter_link_pagamento,
)


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):

    list_display = (
        "numero",
        "nome",
        "modalidade",
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

    @admin.display(
        description="Idade"
    )
    def idade(self, obj):

        return obj.idade_no_evento

    @admin.display(
        description="Pagamento"
    )
    def status_pagamento(self, obj):

        try:

            pagamento = obj.pagamento

        except Pagamento.DoesNotExist:

            return "Sem pagamento"

        return pagamento.get_status_display()

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):

        # Salva a inscrição
        super().save_model(
            request,
            obj,
            form,
            change,
        )

        # Verifica se existe pagamento
        try:

            pagamento = obj.pagamento

        except Pagamento.DoesNotExist:

            # Cria automaticamente
            pagamento = Pagamento.objects.create(

                inscricao=obj,

                valor=obj.valor_total,

                link_pagamento=(
                    obter_link_pagamento(obj)
                ),

                status=Pagamento.PENDENTE,
            )

        # Sincronização
        # Inscrição → Pagamento

        if obj.status == Inscricao.PAGO:

            pagamento.status = (
                Pagamento.PAGO
            )

            if not pagamento.pago_em:

                pagamento.pago_em = (
                    timezone.now()
                )

        elif obj.status == Inscricao.CANCELADO:

            pagamento.status = (
                Pagamento.CANCELADO
            )

            pagamento.pago_em = None

        else:

            pagamento.status = (
                Pagamento.PENDENTE
            )

            pagamento.pago_em = None

        pagamento.valor = (
            obj.valor_total
        )

        pagamento.save()


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

            obj.inscricao.status = (
                Inscricao.PAGO
            )

        elif obj.status == Pagamento.CANCELADO:

            obj.inscricao.status = (
                Inscricao.CANCELADO
            )

            obj.pago_em = None

        else:

            obj.inscricao.status = (
                Inscricao.PENDENTE
            )

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