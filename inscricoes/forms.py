from django import forms

from .models import EVENT_DATE, Inscricao


class InscricaoForm(forms.ModelForm):

    class Meta:
        model = Inscricao

        fields = [
            "nome",
            "telefone",
            "email",
            "data_nascimento",
            "modalidade",
            "tamanho_camisa",
            "militar",
            "comprovante_militar",
            "autorizacao_responsavel",
        ]

        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "tamanho_camisa": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tamanho_camisa"].required = True
        self.fields["tamanho_camisa"].label = "Tamanho da camisa do kit"

        self.fields["tamanho_camisa"].choices = [
            ("", "Selecione o tamanho"),
            *Inscricao.TAMANHOS_CAMISA,
        ]

    def clean(self):
        cleaned_data = super().clean()
        nascimento = cleaned_data.get("data_nascimento")

        if nascimento:
            idade = EVENT_DATE.year - nascimento.year
            if (EVENT_DATE.month, EVENT_DATE.day) < (
                nascimento.month,
                nascimento.day,
            ):
                idade -= 1

            if idade < 12:
                self.add_error(
                    "data_nascimento",
                    "Idade mínima: 12 anos completos em 2026.",
                )

            if idade < 18 and not cleaned_data.get("autorizacao_responsavel"):
                self.add_error(
                    "autorizacao_responsavel",
                    "Obrigatória para menores de 18 anos.",
                )

        if cleaned_data.get("militar") and not cleaned_data.get(
            "comprovante_militar"
        ):
            self.add_error("comprovante_militar", "Envie o comprovante.")

        return cleaned_data
