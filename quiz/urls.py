from django.urls import path
from .views import HomeView, ResultView, BotLinkView

urlpatterns = [
    path('result/', ResultView.as_view(), name='result'),
    path('bot/', BotLinkView.as_view(), name='bot_link'),
    path('', HomeView.as_view(), name='home'),
]
