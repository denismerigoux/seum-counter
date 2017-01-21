from django.conf.urls import url
from counter.rss import SeumFeed
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from .views import views, hashtag, counter, user

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^reset-counter/$', counter.reset_counter, name='reset-counter'),
    url(r'^counter/(?P<id_counter>\d+)/$', counter.get, name='counter'),
    url(r'^hashtag/(?P<keyword>.+)/$', hashtag.get, name='hashtag'),

    url(r'^like/$', views.like, name='like'),
    url(r'^toggle-notif/$', views.toggleEmailNotifications,
        name='toggle_email_notifications'),
    url(r'^toggle-sort-score/$', views.toggleScoreSorting,
        name='toggle_sort_score'),

    url(r'^create_user/$', user.create, name='create_user'),

    url(r'^rss/$', SeumFeed()),

    url(r'^login/$', auth_views.login,
        {'template_name': 'login.html'},
        name='login'),
    url(r'^logout/$', auth_views.logout_then_login,
        name='logout'),
    url(r'^password/change/$', auth_views.password_change,
        {'template_name': 'passwordChange.html'},
        name='password_change'),
    url(r'^password/change/done∕$', auth_views.password_change_done,
        {'template_name': 'passwordChangeDone.html'},
        name='password_change_done'),
    url(r'^password/reset/$', auth_views.password_reset,
        {'template_name': 'passwordReset.html',
         'email_template_name': 'resetEmail.txt',
         'subject_template_name': 'subjectEmail.txt',
         'from_email': 'SeumBook <no-reply@merigoux.ovh>'},
        name='password_reset'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        auth_views.password_reset_confirm,
        {'template_name': 'passwordResetConfirm.html'},
        name='password_reset_confirm'),
    url(r'^password/reset/complete/$',
        auth_views.password_reset_complete,
        {'template_name': 'passwordResetComplete.html'},
        name='password_reset_complete'),
    url(r'^password/reset/done/$',
        auth_views.password_reset_done,
        {'template_name': 'passwordResetDone.html'},
        name='password_reset_done'),
    url(r'^', RedirectView.as_view(pattern_name='home')),
]
