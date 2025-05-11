# quiz/views.py

from django.views.generic import TemplateView
from .models import TelegramUser, UserAnswer

class HomeView(TemplateView):
    template_name = 'home.html'

class ResultView(TemplateView):
    template_name = 'result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = TelegramUser.objects.all()
        user_results = []
        for user in users:
            answers = UserAnswer.objects.filter(user=user).select_related('question', 'selected_option')
            if answers.exists():
                score = answers.filter(is_correct=True).count()
                total = answers.count()
                percentage = (score / total * 100) if total > 0 else 0
            else:
                score = 0
                total = 0
                percentage = 0
            user_results.append({
                'user': user,
                'score': score,
                'total': total,
                'percentage': round(percentage, 2),
            })
        # Foiz bo‘yicha kamayish tartibida saralash
        user_results = sorted(user_results, key=lambda x: x['percentage'], reverse=True)
        context['user_results'] = user_results
        return context

class BotLinkView(TemplateView):
    template_name = 'bot_link.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bot_url'] = "https://t.me/Autoquizzer_Bot"  # O‘z bot URL’ingizni qo‘ying
        return context