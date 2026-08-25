from django.contrib import admin

from .models import (
    Inscricao,
    Pagamento,
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
        "status",
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

    readonly_fields = (
        "numero",
        "lote",
        "valor_inscricao",
        "valor_total",
        "criado_em",
        "atualizado_em",
    )

    @admin.display(
        description="Idade"
    )
    def idade(self, obj):
        return obj.idade_no_evento


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