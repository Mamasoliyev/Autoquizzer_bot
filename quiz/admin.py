from django.contrib import admin
from .models import Question, AnswerOption, TelegramUser

class AnswerInline(admin.TabularInline):
    model = AnswerOption
    extra = 2

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
    inlines = [AnswerInline]

admin.site.register(AnswerOption)

admin.site.register(TelegramUser)