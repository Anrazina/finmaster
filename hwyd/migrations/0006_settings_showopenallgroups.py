# Generated by Django 4.2.4 on 2023-09-08 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hwyd', '0005_settings_fontfamily'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='showOpenAllGroups',
            field=models.BooleanField(default=True, verbose_name='Открыть/закрыть группы'),
            preserve_default=False,
        ),
    ]