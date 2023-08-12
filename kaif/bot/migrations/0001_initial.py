# Generated by Django 4.2.1 on 2023-05-30 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(max_length=150, verbose_name='Ник')),
                ('date', models.CharField(max_length=50, verbose_name='Дата публикации')),
                ('content', models.TextField(verbose_name='Комментарий')),
            ],
        ),
    ]
