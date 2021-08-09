# Generated by Django 1.11.20 on 2019-08-07 22:23


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    replaces = [('challenge', '0008_auto_20190807_1808'), ('challenge', '0009_auto_20190807_1813'), ('challenge', '0010_auto_20190807_1910'), ('challenge', '0011_auto_20190807_2138')]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('challenge', '0007_auto_20190212_2242'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='challenge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='challenge.Challenge'),
        ),
        migrations.AddField(
            model_name='entry',
            name='group_url',
            field=models.URLField(blank=True, help_text='Chat/group URL, visible only to participants.', null=True),
        ),
        migrations.AddField(
            model_name='entry',
            name='is_open',
            field=models.BooleanField(default=False, help_text='Can people request to join the team?'),
        ),
        migrations.AddField(
            model_name='entry',
            name='join_requests',
            field=models.ManyToManyField(related_name='join_request_entries', to=settings.AUTH_USER_MODEL),
        ),
    ]
