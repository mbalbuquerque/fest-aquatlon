from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "inscricao/",
        views.nova_inscricao,
        name="nova_inscricao",
    ),

    path(
        "pagamento/<str:numero>/",
        views.pagamento,
        name="pagamento",
    ),

    path(
        "inscricao/sucesso/<str:numero>/",
        views.sucesso,
        name="sucesso",
    ),

    path(
        "webhooks/mercadopago/",
        views.webhook_mercadopago,
        name="webhook_mercadopago",
    ),

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard",
    ),

    path(
    "extrato-financeiro/",
    views.extrato_financeiro,
    name="extrato_financeiro",
),
    
path(
    "relatorios/",
    views.relatorios,
    name="relatorios",
),

path(
    "exportar-excel/",
    views.exportar_excel,
    name="exportar_excel",
), 
]