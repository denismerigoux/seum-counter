from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^seum/', views.home),
    url(r'^reset-counter/',views.resetCounter),
    url(r'^counter/(?P<id_counter>\d+)$', views.counter),
]
