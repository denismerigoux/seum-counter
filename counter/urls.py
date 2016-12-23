from django.conf.urls import url
from counter.rss import SeumFeed

from . import views

urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^reset-counter', views.resetCounter, name="reset-counter"),
    url(r'^counter/(?P<id_counter>\d+)$', views.counter, name="counter"),
    url(r'^set-my-counter', views.setMyCounter, name="set-my-counter"),
    url(r'^reset-my-counter', views.resetMyCounter, name="reset-my-counter"),
    url(r'^rss', SeumFeed())
]
