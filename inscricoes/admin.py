from django.contrib import admin
from django.utils import timezone

from .models import Inscricao, Pagamento


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

    @admin.display(description="Idade")
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

    def save_model(self, request, obj, form, change):

        if obj.status == Pagamento.PAGO:
            obj.pago_em = obj.pago_em or timezone.now()

            obj.inscricao.status = Inscricao.PAGO
            obj.inscricao.save(
                update_fields=[
                    "status",
                    "atualizado_em",
                ]
            )

        elif obj.status in [
            Pagamento.PENDENTE,
            Pagamento.CANCELADO,
            Pagamento.EXPIRADO,
        ]:
            obj.inscricao.status = Inscricao.PENDENTE

            obj.inscricao.save(
                update_fields=[
                    "status",
                    "atualizado_em",
                ]
            )

        super().save_model(
            request,
            obj,
            form,
            change,
        )