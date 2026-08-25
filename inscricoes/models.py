from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


EVENT_DATE = timezone.datetime(2026, 12, 20).date()
PROMO_END = timezone.datetime(2026, 9, 20).date()
LOT_END = timezone.datetime(2026, 11, 5).date()

MAX_SLOTS = 180


class Inscricao(models.Model):
    MINI = "MINI"
    SPRINT = "SPRINT"

    MODALIDADES = [
        (
            MINI,
            "Mini Sprint — 500m natação + 2,5km corrida",
        ),
        (
            SPRINT,
            "Sprint — 1km natação + 5km corrida",
        ),
    ]

    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    CANCELADO = "CANCELADO"

    STATUS = [
        (PENDENTE, "Aguardando pagamento"),
        (PAGO, "Pagamento confirmado"),
        (CANCELADO, "Cancelada"),
    ]

    numero = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    nome = models.CharField(
        max_length=150,
    )

    telefone = models.CharField(
        max_length=30,
    )

    email = models.EmailField()

    data_nascimento = models.DateField()

    modalidade = models.CharField(
        max_length=10,
        choices=MODALIDADES,
    )

    militar = models.BooleanField(
        default=False,
    )

    comprovante_militar = models.FileField(
        upload_to="comprovantes/militares/",
        blank=True,
        null=True,
    )

    autorizacao_responsavel = models.FileField(
        upload_to="comprovantes/responsaveis/",
        blank=True,
        null=True,
    )

    lote = models.CharField(
        max_length=40,
        blank=True,
    )

    valor_inscricao = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    valor_total = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS,
        default=PENDENTE,
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"

    def __str__(self):
        return f"{self.numero or 'Nova'} — {self.nome}"

    @property
    def idade_no_evento(self):
        nascimento = self.data_nascimento

        idade = EVENT_DATE.year - nascimento.year

        if (
            EVENT_DATE.month,
            EVENT_DATE.day,
        ) < (
            nascimento.month,
            nascimento.day,
        ):
            idade -= 1

        return idade

    def definir_valor(self):
        """
        Define lote, valor e link de pagamento
        conforme a data, idade e condição do atleta.
        """

        data = timezone.localdate()
        idade = self.idade_no_evento

        if data > LOT_END:
            raise ValidationError(
                "As inscrições estão encerradas."
            )

        # LOTE PROMOCIONAL
        if data <= PROMO_END:
            self.lote = "Promocional"

            self.valor_inscricao = Decimal("154.00")
            self.valor_total = Decimal("154.00")

            return

        # SEGUNDO LOTE
        self.lote = "Segundo lote"

        # MILITAR
        if self.militar:
            self.valor_inscricao = Decimal("162.00")
            self.valor_total = Decimal("162.00")

        # MENOR DE 17 OU 60+
        elif idade < 17 or idade >= 60:
            self.valor_inscricao = Decimal("154.00")
            self.valor_total = Decimal("154.00")

        # 17 A 59
        else:
            self.valor_inscricao = Decimal("174.00")
            self.valor_total = Decimal("174.00")

    def clean(self):
        idade = self.idade_no_evento

        if idade < 12:
            raise ValidationError(
                "A idade mínima é 12 anos completos em 2026."
            )

        if idade < 18 and not self.autorizacao_responsavel:
            raise ValidationError(
                "Menores de 18 anos precisam da autorização "
                "do responsável."
            )

        if self.militar and not self.comprovante_militar:
            raise ValidationError(
                "Militares devem apresentar documento comprobatório."
            )

    def save(self, *args, **kwargs):

        creating = not self.pk

        if creating:
            super().save(*args, **kwargs)

            self.numero = f"FA26-{self.pk:04d}"

        self.definir_valor()

        super().save(*args, **kwargs)


class Pagamento(models.Model):

    PENDENTE = "PENDENTE"
    PAGO = "PAGO"
    CANCELADO = "CANCELADO"
    EXPIRADO = "EXPIRADO"

    STATUS = [
        (PENDENTE, "Pendente"),
        (PAGO, "Pago"),
        (CANCELADO, "Cancelado"),
        (EXPIRADO, "Expirado"),
    ]

    MERCADO_PAGO = "MERCADO_PAGO"

    inscricao = models.OneToOneField(
        Inscricao,
        on_delete=models.CASCADE,
        related_name="pagamento",
    )

    plataforma = models.CharField(
        max_length=30,
        default=MERCADO_PAGO,
    )

    valor = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    link_pagamento = models.URLField(
        max_length=1000,
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS,
        default=PENDENTE,
    )

    metodo = models.CharField(
        max_length=30,
        blank=True,
    )

    identificador_transacao = models.CharField(
    max_length=150,
    blank=True,
    db_index=True,
)

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    pago_em = models.DateTimeField(
        null=True,
        blank=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ["-criado_em"]

    def __str__(self):
        return (
            f"{self.inscricao.numero} - "
            f"R$ {self.valor}"
        )