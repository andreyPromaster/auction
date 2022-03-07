# Generated by Django 3.1.7 on 2021-04-06 08:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction_app', '0003_baseauction_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseauction',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Pending'), (1, 'In Progress'), (2, 'Completed')], default=0),
        ),
    ]