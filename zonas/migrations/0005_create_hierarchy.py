from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zonas', '0004_alter_zona_options_zona_cobrador_zona_codigo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Departamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'verbose_name': 'Departamento',
                'verbose_name_plural': 'Departamentos',
            },
        ),
        migrations.CreateModel(
            name='Provincia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('departamento', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='provincias', to='zonas.departamento')),
            ],
            options={
                'verbose_name': 'Provincia',
                'verbose_name_plural': 'Provincias',
                'unique_together': {('departamento', 'nombre')},
            },
        ),
        migrations.CreateModel(
            name='Distrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('provincia', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='distritos', to='zonas.provincia')),
            ],
            options={
                'verbose_name': 'Distrito',
                'verbose_name_plural': 'Distritos',
                'unique_together': {('provincia', 'nombre')},
            },
        ),
        migrations.CreateModel(
            name='Caserio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('codigo', models.CharField(blank=True, default='', max_length=20)),
                ('activa', models.BooleanField(default=True)),
                ('distrito', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='caserios', to='zonas.distrito')),
            ],
            options={
                'verbose_name': 'Caserío',
                'verbose_name_plural': 'Caseríos',
                'unique_together': {('distrito', 'nombre')},
            },
        ),
    ]
