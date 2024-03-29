# Generated by Django 3.2.6 on 2021-08-09 08:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20190807_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersettings',
            name='email_contest_updates',
            field=models.BooleanField(default=True, help_text='Can we e-mail you about contests you are registered in?'),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='email_news',
            field=models.BooleanField(default=True, help_text='Can we e-mail you (rarely) about Pyweek news, such as upcoming competitions?'),
        ),
        migrations.AlterField(
            model_name='usersettings',
            name='email_replies',
            field=models.BooleanField(default=True, help_text='Do you want to receive replies to your diary posts and comments by e-mail?'),
        ),
    ]
