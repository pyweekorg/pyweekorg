# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-14 19:13
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import pyweek.challenge.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Award',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('content', models.FileField(upload_to=pyweek.challenge.models.award_upload_location)),
                ('description', models.CharField(max_length=255)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='Challenge',
            fields=[
                ('number', models.IntegerField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100)),
                ('start', models.DateField()),
                ('end', models.DateField()),
                ('motd', models.TextField()),
                ('is_rego_open', models.BooleanField(default=False)),
                ('theme', models.CharField(blank=True, default=b'', max_length=100, null=True)),
                ('torrent_url', models.CharField(blank=True, default=b'', max_length=255, null=True)),
            ],
            options={
                'ordering': ['start'],
            },
        ),
        migrations.CreateModel(
            name='Checksum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('description', models.CharField(max_length=255)),
                ('md5', models.CharField(max_length=32, unique=True, validators=[django.core.validators.RegexValidator(b'[0-9a-fA-F]{32}', b'Invalid md5 hash. Should be 32 hex digits')])),
                ('is_final', models.BooleanField(default=False)),
                ('is_screenshot', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='DiaryComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created', models.DateTimeField()),
                ('edited', models.DateTimeField(null=True)),
                ('challenge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
            ],
            options={
                'ordering': ['created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='DiaryEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField()),
                ('created', models.DateTimeField()),
                ('edited', models.DateTimeField(blank=True, null=True)),
                ('activity', models.DateTimeField()),
                ('reply_count', models.PositiveIntegerField(default=0)),
                ('sticky', models.BooleanField(default=False)),
                ('is_pyggy', models.BooleanField(default=False)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actor', to=settings.AUTH_USER_MODEL)),
                ('challenge', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
            ],
            options={
                'ordering': ['-created', 'title'],
                'get_latest_by': 'activity',
                'verbose_name_plural': 'DiaryEntries',
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('name', models.SlugField(max_length=15, primary_key=True, serialize=False)),
                ('title', models.CharField(help_text=b'The name of the team that created the entry.', max_length=100)),
                ('game', models.CharField(help_text=b'The name of the game itself.', max_length=100)),
                ('description', models.TextField()),
                ('is_upload_open', models.BooleanField(default=False)),
                ('has_final', models.BooleanField(default=False)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='challenge', to='challenge.Challenge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owner', to=settings.AUTH_USER_MODEL, verbose_name=b'entry owner')),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('winner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='winner', to='challenge.Challenge')),
            ],
            options={
                'ordering': ['-challenge', 'name'],
                'verbose_name_plural': 'entries',
            },
        ),
        migrations.CreateModel(
            name='EntryAward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('award', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Award')),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry')),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('thumb_width', models.PositiveIntegerField(default=0)),
                ('content', models.FileField(upload_to=pyweek.challenge.models.file_upload_location)),
                ('created', models.DateTimeField()),
                ('description', models.CharField(max_length=255)),
                ('is_final', models.BooleanField(default=False)),
                ('is_screenshot', models.BooleanField(default=False)),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('created', models.DateTimeField()),
                ('is_open', models.BooleanField()),
                ('is_hidden', models.BooleanField()),
                ('is_ongoing', models.BooleanField()),
                ('type', models.IntegerField(choices=[(0, b'Ten Single Votes'), (1, b'Select Many'), (2, b'Instant-Runoff'), (3, b'Poll')])),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='Rating',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fun', models.PositiveIntegerField(choices=[(1, b'Not at all'), (2, b'Below average'), (3, b'About average'), (4, b'Above average'), (5, b'Exceptional')], default=3)),
                ('innovation', models.PositiveIntegerField(choices=[(1, b'Not at all'), (2, b'Below average'), (3, b'About average'), (4, b'Above average'), (5, b'Exceptional')], default=3)),
                ('production', models.PositiveIntegerField(choices=[(1, b'Not at all'), (2, b'Below average'), (3, b'About average'), (4, b'Above average'), (5, b'Exceptional')], default=3)),
                ('nonworking', models.BooleanField()),
                ('disqualify', models.BooleanField()),
                ('comment', models.TextField()),
                ('created', models.DateTimeField()),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='RatingTally',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('individual', models.BooleanField()),
                ('fun', models.FloatField()),
                ('innovation', models.FloatField()),
                ('production', models.FloatField()),
                ('overall', models.FloatField()),
                ('nonworking', models.PositiveIntegerField()),
                ('disqualify', models.PositiveIntegerField()),
                ('respondents', models.PositiveIntegerField()),
                ('challenge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Challenge')),
                ('entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry')),
            ],
            options={
                'ordering': ['challenge', 'individual', '-overall'],
                'verbose_name_plural': 'RatingTallies',
            },
        ),
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('value', models.IntegerField()),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Option')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Poll')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='option',
            name='poll',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Poll'),
        ),
        migrations.AddField(
            model_name='diaryentry',
            name='entry',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry'),
        ),
        migrations.AddField(
            model_name='diaryentry',
            name='last_comment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='challenge.DiaryComment'),
        ),
        migrations.AddField(
            model_name='diaryentry',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='author', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='diarycomment',
            name='diary_entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.DiaryEntry'),
        ),
        migrations.AddField(
            model_name='diarycomment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='checksum',
            name='entry',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='challenge.Entry'),
        ),
        migrations.AddField(
            model_name='checksum',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='challenge',
            name='theme_poll',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='poll_challenge', to='challenge.Poll'),
        ),
        migrations.AlterUniqueTogether(
            name='response',
            unique_together=set([('option', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='rating',
            unique_together=set([('entry', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='option',
            unique_together=set([('poll', 'text')]),
        ),
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together=set([('challenge', 'title'), ('challenge', 'name')]),
        ),
    ]