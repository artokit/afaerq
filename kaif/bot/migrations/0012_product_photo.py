# Generated by Django 4.2.1 on 2023-08-12 02:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0011_product_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Фотография'),
        ),
    ]
