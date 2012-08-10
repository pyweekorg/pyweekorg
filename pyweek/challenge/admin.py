from django.contrib import admin

from challenge import models


class OptionAdmin(admin.ModelAdmin):
    fields = ['poll', 'text']

class ResponseAdmin(admin.ModelAdmin):
    fields = ['poll', 'option', 'user', 'created', 'value']

class PollAdmin(admin.ModelAdmin):
    field = ['challenge', 'title', 'created', 'is_open',
             'is_hidden', 'is_ongoing', 'type']

class ChecksumAdmin(admin.ModelAdmin):
    fields = ['user', 'created', 'md5', 'is_final',
              'is_screenshot']

class EntryAwardAdmin(admin.ModelAdmin):
    fields = ['creator', 'entry', 'award']

class AwardAdmin(admin.ModelAdmin):
    fields = ['creator', 'description']

class FileAdmin(admin.ModelAdmin):
    fields = ['user', 'created', 'filename', 'is_final',
              'is_screenshot']

class DiaryCommentAdmin(admin.ModelAdmin):
    fields = ['user', 'created', 'diary_entry']

class DiaryEntryAdmin(admin.ModelAdmin):
    fields = ['user', 'created', 'title']

class RatingTallyAdmin(admin.ModelAdmin):
    fields = ['entry', 'individual', 'overall', 'disqualify', 'fun',
              'innovation', 'production', 'respondents']

class RatingAdmin(admin.ModelAdmin):
    fields = ['entry', 'user', 'created', 'disqualify', 'fun',
              'innovation', 'production']

class EntryAdmin(admin.ModelAdmin):
    fields = ['name', 'title', 'game', 'user', 'users',
              'challenge', 'is_upload_open']

class ChallengeAdmin(admin.ModelAdmin):
    fields = ['title', 'start', 'end', 'is_rego_open']


admin.site.register(models.Challenge, ChallengeAdmin)
admin.site.register(models.Entry, EntryAdmin)
admin.site.register(models.RatingTally, RatingTallyAdmin)
admin.site.register(models.DiaryEntry, DiaryEntryAdmin)
admin.site.register(models.EntryAward, EntryAwardAdmin)
admin.site.register(models.Award, AwardAdmin)
admin.site.register(models.Checksum, ChecksumAdmin)
admin.site.register(models.Poll, PollAdmin)
admin.site.register(models.Option, OptionAdmin)
admin.site.register(models.Response, ResponseAdmin)

