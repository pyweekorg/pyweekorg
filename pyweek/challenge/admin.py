from django.contrib import admin
from pyweek.challenge import models

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .views.user import delete_spammer
from . import models


admin.site.unregister(User)

def do_delete_spammer(modeladmin, request, queryset):
    for obj in queryset:
        delete_spammer(request, obj.username)
do_delete_spammer.short_description = 'Delete that spammer!'

class CustomUserAdmin(UserAdmin):

    actions = [do_delete_spammer]

admin.site.register(User, CustomUserAdmin)


class OptionAdmin(admin.ModelAdmin):
    list_display = ['poll', 'text']


class ResponseAdmin(admin.ModelAdmin):
    list_display = ['poll', 'option', 'user', 'created', 'value']



class OptionInline(admin.TabularInline):
    model = models.Option
    max_num = 5
    min_num = 5


class PollAdmin(admin.ModelAdmin):
    field = ['challenge', 'title', 'created', 'is_open',
             'is_hidden', 'is_ongoing', 'type']
    inlines = [OptionInline]


class EntryAwardAdmin(admin.ModelAdmin):
    list_display = ['creator', 'entry', 'award']


class AwardAdmin(admin.ModelAdmin):
    list_display = ['creator', 'description']


class FileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created', 'filename', 'is_final',
                    'is_screenshot']


class DiaryCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'created', 'diary_entry']


class DiaryEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created']
    search_fields = ['user', 'title']
    list_filter = ['sticky']


class RatingTallyAdmin(admin.ModelAdmin):
    list_display = ['entry', 'individual', 'overall', 'disqualify', 'fun',
                    'innovation', 'production', 'respondents']


class RatingAdmin(admin.ModelAdmin):
    list_display = ['entry', 'user', 'created', 'disqualify', 'fun',
                    'innovation', 'production']


class EntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'game', 'user',
                    'challenge', 'is_upload_open']
    search_fields = ['name', 'title']
    list_filter = ['challenge']


class ChallengeAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'start', 'end', 'is_rego_open']


admin.site.register(models.Challenge, ChallengeAdmin)
admin.site.register(models.Entry, EntryAdmin)
admin.site.register(models.RatingTally, RatingTallyAdmin)
admin.site.register(models.DiaryEntry, DiaryEntryAdmin)
admin.site.register(models.EntryAward, EntryAwardAdmin)
admin.site.register(models.Award, AwardAdmin)
admin.site.register(models.Poll, PollAdmin)
admin.site.register(models.Option, OptionAdmin)
admin.site.register(models.Response, ResponseAdmin)
