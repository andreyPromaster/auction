# Generated by Django 3.1.7 on 2021-03-19 12:40

import auction_app.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auction_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='dutchauction',
            name='start_price',
            field=auction_app.models.CurrencyField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='baseauction',
            name='current_price',
            field=auction_app.models.CurrencyField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='dutchauction',
            name='end_price',
            field=auction_app.models.CurrencyField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='englishauction',
            name='reserved_price',
            field=auction_app.models.CurrencyField(decimal_places=2, max_digits=10, verbose_name='Reserved price'),
        ),
    ]
