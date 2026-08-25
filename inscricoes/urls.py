from django.urls import path
from . import views
urlpatterns=[path("",views.home,name="home"),path("inscricao/",views.nova_inscricao,name="nova_inscricao"),path("inscricao/sucesso/<str:numero>/",views.sucesso,name="sucesso")]
