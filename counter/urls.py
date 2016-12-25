from django.conf.urls import url
from counter.rss import SeumFeed
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    url(r'^$', views.home, name="home"),
    url(r'^reset-counter', views.resetCounter, name="reset-counter"),
    url(r'^counter/(?P<id_counter>\d+)$', views.counter, name="counter"),
    url(r'^rss', SeumFeed()),
    url(r'^login', auth_views.login,
        {'template_name': 'login.html'},
        name="login"),
    url(r'^logout', auth_views.logout,
        {'next_page': 'login'},
        name='logout')
]
