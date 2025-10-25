from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0002_cliente_apellido_cliente_dia_vencimiento_and_more'),
        ('zonas', '0005_create_hierarchy'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='caserio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='zonas.caserio', verbose_name='Caserío asignado'),
        ),
    ]
