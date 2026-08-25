from django import forms
from .models import Inscricao,EVENT_DATE
class InscricaoForm(forms.ModelForm):
    class Meta:
        model=Inscricao
        fields=["nome","telefone","email","data_nascimento","modalidade","militar","comprovante_militar","autorizacao_responsavel"]
        widgets={"data_nascimento":forms.DateInput(attrs={"type":"date"})}
    def clean(self):
        c=super().clean(); b=c.get("data_nascimento")
        if b:
            age=EVENT_DATE.year-b.year
            if (EVENT_DATE.month,EVENT_DATE.day)<(b.month,b.day): age-=1
            if age<12: self.add_error("data_nascimento","Idade mínima: 12 anos completos em 2026.")
            if age<18 and not c.get("autorizacao_responsavel"): self.add_error("autorizacao_responsavel","Obrigatória para menores de 18 anos.")
        if c.get("militar") and not c.get("comprovante_militar"): self.add_error("comprovante_militar","Envie o comprovante.")
        return c
