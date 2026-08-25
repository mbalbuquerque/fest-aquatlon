from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
EVENT_DATE=timezone.datetime(2026,12,20).date()
PROMO_END=timezone.datetime(2026,9,20).date()
LOT_END=timezone.datetime(2026,11,7).date()
FEE=Decimal("6.80")
class Inscricao(models.Model):
    MINI="MINI"; SPRINT="SPRINT"
    MODALIDADES=[(MINI,"Mini Sprint — 500m natação + 2,5km corrida"),(SPRINT,"Sprint — 1km natação + 5km corrida")]
    PENDENTE="PENDENTE"; PAGO="PAGO"; CANCELADO="CANCELADO"
    STATUS=[(PENDENTE,"Aguardando pagamento"),(PAGO,"Pagamento confirmado"),(CANCELADO,"Cancelada")]
    numero=models.CharField(max_length=20,unique=True,blank=True)
    nome=models.CharField(max_length=150); telefone=models.CharField(max_length=30); email=models.EmailField()
    data_nascimento=models.DateField(); modalidade=models.CharField(max_length=10,choices=MODALIDADES)
    militar=models.BooleanField(default=False)
    comprovante_militar=models.FileField(upload_to="comprovantes/militares/",blank=True,null=True)
    autorizacao_responsavel=models.FileField(upload_to="comprovantes/responsaveis/",blank=True,null=True)
    lote=models.CharField(max_length=30,blank=True)
    valor_inscricao=models.DecimalField(max_digits=8,decimal_places=2,default=0)
    taxa_servico=models.DecimalField(max_digits=8,decimal_places=2,default=FEE)
    valor_total=models.DecimalField(max_digits=8,decimal_places=2,default=0)
    status=models.CharField(max_length=12,choices=STATUS,default=PENDENTE)
    criado_em=models.DateTimeField(auto_now_add=True); atualizado_em=models.DateTimeField(auto_now=True)
    @property
    def idade_no_evento(self):
        d=self.data_nascimento; a=EVENT_DATE.year-d.year
        return a-1 if (EVENT_DATE.month,EVENT_DATE.day)<(d.month,d.day) else a
    def calcular_valores(self):
        data=timezone.localdate(); age=self.idade_no_evento
        if data>LOT_END: raise ValidationError("Inscrições encerradas.")
        if data<=PROMO_END: base=Decimal("145"); self.lote="Promocional"
        else:
            self.lote="Segundo lote"
            base=Decimal("155") if self.militar else (Decimal("145") if age<17 or age>60 else Decimal("167"))
        self.valor_inscricao=base; self.taxa_servico=FEE; self.valor_total=base+FEE
    def clean(self):
        if self.idade_no_evento<12: raise ValidationError("Idade mínima: 12 anos completos em 2026.")
        if self.idade_no_evento<18 and not self.autorizacao_responsavel: raise ValidationError("Autorização do responsável obrigatória.")
        if self.militar and not self.comprovante_militar: raise ValidationError("Comprovante militar obrigatório.")
    def save(self,*args,**kwargs):
        creating=not self.pk
        if creating: super().save(*args,**kwargs); self.numero=f"FA26-{self.pk:04d}"
        self.calcular_valores(); super().save(*args,**kwargs)
    class Meta:
        ordering=["-criado_em"]; verbose_name="Inscrição"; verbose_name_plural="Inscrições"
    def __str__(self): return f"{self.numero or 'Nova'} — {self.nome}"
