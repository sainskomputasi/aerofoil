# Generated by Django 3.2.5 on 2021-09-20 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flow', '0005_auto_20210917_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='koleksiairfoil',
            name='mach',
            field=models.FloatField(default=0.1),
        ),
    ]