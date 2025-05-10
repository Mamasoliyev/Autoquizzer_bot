from django.contrib import admin
from .models import Question, AnswerOption, TelegramUser

class AnswerInline(admin.TabularInline):
    model = AnswerOption
    extra = 2  # You can customize the number of extra fields

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
    inlines = [AnswerInline]  # This will show the answer options in the admin panel

admin.site.register(AnswerOption)
admin.site.register(TelegramUser)