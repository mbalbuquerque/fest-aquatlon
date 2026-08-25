from django.shortcuts import get_object_or_404,redirect,render
from .forms import InscricaoForm
from .models import Inscricao
def home(request): return render(request,"inscricoes/home.html")
def nova_inscricao(request):
    vagas=180-Inscricao.objects.exclude(status=Inscricao.CANCELADO).count()
    if vagas<=0: return render(request,"registration/encerradas.html")
    form=InscricaoForm(request.POST or None,request.FILES or None)
    if request.method=="POST" and form.is_valid():
        i=form.save(commit=False); i.save(); return redirect("sucesso",numero=i.numero)
    return render(request,"registration/inscricao.html",{"form":form,"vagas":vagas})
def sucesso(request,numero):
    return render(request,"registration/sucesso.html",{"inscricao":get_object_or_404(Inscricao,numero=numero)})
