from django.contrib import admin
from .models import Question, AnswerOption, TelegramUser, UserAnswer


class AnswerInline(admin.TabularInline):
    model = AnswerOption
    extra = 2  # You can customize the number of extra fields


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'created_at')
    inlines = [AnswerInline]  # This will show the answer options in the admin panel


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'selected_option', 'is_correct', 'answered_at')
    list_filter = ('is_correct', 'answered_at', 'user')
    search_fields = ('user__full_name', 'user__username', 'question__text', 'selected_option__text')
    readonly_fields = ('answered_at',)
    list_per_page = 25  # Har sahifada 25 ta yozuv ko‘rsatiladi

    # Ko‘rsatiladigan maydonlar uchun maxsus metodlar
    def user(self, obj):
        return f"{obj.user.full_name} (@{obj.user.username or 'username yo‘q'})"

    user.short_description = "Foydalanuvchi"

    def question(self, obj):
        return obj.question.text[:50]  # Savol matnini qisqartirish

    question.short_description = "Savol"

    def selected_option(self, obj):
        return obj.selected_option.text

    selected_option.short_description = "Tanlangan javob"


admin.site.register(AnswerOption)
admin.site.register(TelegramUser)
