import uuid

from django.db import migrations


def preencher_tokens_publicos(apps, schema_editor):
    Inscricao = apps.get_model("inscricoes", "Inscricao")

    inscricoes = Inscricao.objects.filter(
        token_publico__isnull=True
    )

    for inscricao in inscricoes.iterator():
        inscricao.token_publico = uuid.uuid4()
        inscricao.save(update_fields=["token_publico"])


class Migration(migrations.Migration):

    dependencies = [
        ("inscricoes", "0006_inscricao_token_publico"),
    ]

    operations = [
        migrations.RunPython(
            preencher_tokens_publicos,
            migrations.RunPython.noop,
        ),
    ]