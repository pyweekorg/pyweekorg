# Generated by Django 1.11 on 2018-10-03 22:56


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersettings',
            name='email_replies',
            field=models.BooleanField(default=True, help_text='Do you want to receive replies to your diary posts and comments by e-mail?'),
        ),
    ]
