from django.conf.urls import url
from counter.rss import SeumFeed
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from .views import telegram

urlpatterns = [
    url(r'^webhook/$', telegram.webhook, name='telwebhook'),
    url(r'^link/telegram/(?P<verif_key>.+)/$', telegram.link, name='tellink'),
]
