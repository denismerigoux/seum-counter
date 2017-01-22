import copy
from datetime import datetime, timedelta
import math

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db.models import Prefetch, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext as _, get_language

import arrow
from babel.dates import format_timedelta, format_datetime
from graphos.renderers import gchart
from graphos.sources.model import ModelDataSource
from graphos.sources.simple import SimpleDataSource
import numpy as np
import pandas as pd

from counter.models import *
from counter.utils import parseSeumReason


# Number of counters displayed on the home page's best seumeurs graph
bestSeumeursNumber = 15


@login_required
def index(request):
    # Used later to keep track of the maximum JSS
    lastResets = []
    no_seum_delta = timedelta.max

    # First select our counter
    try:
        myCounter = Counter.objects.get(user__id=request.user.id)
        myLastReset = Reset.objects.select_related('who').filter(counter=myCounter).order_by('-timestamp').first()

        if myLastReset is None:
            # This person never had the seum
            myCounter.lastReset = Reset()
            myCounter.lastReset.delta = no_seum_delta
            myCounter.lastReset.formatted_delta = format_timedelta(myCounter.lastReset.delta, locale=get_language(), threshold=1)
            myCounter.lastReset.noSeum = True
        else:
            myCounter.lastReset = myLastReset
            myCounter.lastReset.noSeum = False
            if myCounter.lastReset.who is None or myCounter.lastReset.who.id == myCounter.id:
                myCounter.lastReset.selfSeum = True
            else:
                myCounter.lastReset.selfSeum = False
            likesMe = list(Like.objects.select_related('liker').filter(reset=myCounter.lastReset))
            myCounter.likeCount = len(likesMe)
            if myCounter.likeCount > 0:
                myCounter.likersString = ", ".join([like.liker.trigramme for like in likesMe])
            myCounter.lastReset.formatted_delta = arrow.Arrow.fromdatetime(myCounter.lastReset.timestamp).humanize(locale=get_language())

    except Counter.DoesNotExist:
        return HttpResponseRedirect(reverse('login'))

    # Building data for counters display
    counters = Counter.objects.prefetch_related(
        'resets__likes',
        Prefetch(
            'resets',
            queryset=Reset.objects.prefetch_related('who', Prefetch('likes', queryset=Like.objects.select_related('liker'))).order_by('-timestamp'),
            to_attr='lastReset'
        )
    )
    for counter in counters:
        # Only the last reset is displayed
        lastReset = list(counter.lastReset)
        if len(lastReset) == 0:  # This person never had the seum
            counter.lastReset = Reset()
            counter.lastReset.delta = no_seum_delta
            counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta, locale=get_language(), threshold=1)
            counter.lastReset.noSeum = True
            counter.lastReset.likes_count = -1
            counter.CSSclass = "warning"
        else:  # This person already had the seum
            counter.lastReset = lastReset[0]
            # To display the last seum we have to know if it is self-inflicted
            if counter.lastReset.who is None or counter.lastReset.who == counter:
                counter.lastReset.selfSeum = True
            else:
                counter.lastReset.selfSeum = False
            # Now we compute the duration since the reset
            counter.lastReset.noSeum = False
            counter.lastReset.delta = datetime.now() - counter.lastReset.timestamp.replace(tzinfo=None)
            # Defining CSS attributes for the counter
            counter.CSSclass = 'primary' if counter == myCounter else 'default'
            # Computing the total number of likes for this counter
            likesMe = list(counter.lastReset.likes.all())
            counter.lastReset.likes_count = len(likesMe)
            counter.alreadyLiked = myCounter in likesMe
            if counter.lastReset.likes_count > 0:
                counter.likersString = ", ".join([like.liker.trigramme for like in likesMe])
            counter.lastReset.formatted_delta = arrow.Arrow.fromdatetime(counter.lastReset.timestamp).humanize(locale=get_language())

        counter.likeCount = counter.lastReset.likes_count
        counter.isHidden = 'hidden'

    if myCounter.sort_by_score:
        # Now we sort the counters according to a reddit-like ranking formula
        # We take into account the number of likes of a reset and recentness
        # The log on the score will give increased value to the first likes
        # The counters with no seum have a like count of -1 by convention
        sorting_key = lambda t: - (math.log(t.lastReset.likes_count + 2) / (1 + (t.lastReset.delta.total_seconds()) / (24 * 3600)))
        counters = sorted(counters, key=sorting_key)
    else:
        counters = sorted(counters, key=lambda t: + t.lastReset.delta.total_seconds())


    # ### GRAPHS ###
    resets_raw = list(Reset.objects.select_related('who', 'counter').annotate(likes_count=Count('likes')))
    likes_raw = list(Like.objects.select_related('liker', 'reset__counter').all())
    hashtags_raw = list(Hashtag.objects.select_related('keyword').all())
    # Prepare pandas.DataFrames to efficiently process the data
    # About the counters
    resets_cols = ['date', 'counter', 'counter_trigram', 'who', 'who_trigram', 'reason', 'likes_count']
    resets_data = [[r.timestamp, r.counter.id, r.counter.trigramme, r.who, r.who, r.reason, r.likes_count] for r in resets_raw]
    for r in resets_data:
        r[3] = 0 if r[3] is None else r[3].id
        r[4] = '' if r[4] is None else r[4].trigramme
    resets_df = pd.DataFrame(resets_data, columns=resets_cols)
    resets_df['timestamp'] = resets_df.date.map(lambda d: d.timestamp())
    resets_df['self_seum'] = (resets_df.who.eq(np.zeros(resets_df.shape[0])) | resets_df.who.eq(resets_df.counter)).map(float)
    resets_df['formatted_delta'] = resets_df.date.map(lambda d: arrow.Arrow.fromdatetime(d).humanize(locale=get_language()))
    # About the likes
    likes_cols = ['liker', 'liker_trigram', 'counter', 'counter_trigram']
    likes_data = [[l.liker.id, l.liker.trigramme, l.reset.counter.id, l.reset.counter.trigramme] for l in likes_raw]
    likes_df = pd.DataFrame(likes_data, columns=likes_cols)
    # About the hashtags
    hashtags_cols = ['keyword']
    hashtags_data = [[h.keyword.text] for h in hashtags_raw]
    hashtags_df = pd.DataFrame(hashtags_data, columns=hashtags_cols)


    # Timeline graph
    timeline_resets = resets_df[resets_df.date > (datetime.now() - timedelta(days=1))].copy().reset_index()
    if timeline_resets.shape[0] == 0:
        noTimeline = True
        line_chart = None
    else:
        noTimeline = False

        # Construct legend for timeline dots
        legend_ = np.zeros(timeline_resets.shape[0], dtype=np.object)
        for i in range(timeline_resets.shape[0]):
            row = timeline_resets.iloc[i]
            if row['self_seum'] == 1:
                legend_[i] = _('%(counter)s: %(reason)s') % {'counter': row['counter_trigram'], 'reason': row['reason']}
            else:
                legend_[i] = _('%(who)s to %(counter)s: %(reason)s') % {'who': row['who_trigram'], 'counter': row['counter_trigram'], 'reason': row['reason']}
        timeline_resets['legend'] = legend_

        # Generate graph
        resets_ = [['', _('Seum')]]
        for i in range(timeline_resets.shape[0]):
            r = timeline_resets.iloc[i]
            resets_.append([{'v': r.timestamp, 'f': r.formatted_delta}, {'v': 0, 'f': r.legend}])
            # resets_.append({
            #     'timestamp': {'v': r.date.timestamp(), 'f': r.formatted_delta},
            #     'Seum': {'v': 0, 'f': r.legend},
            # })
        line_data = SimpleDataSource(resets_)
        line_chart = gchart.LineChart(line_data, options={
            'lineWidth': 0,
            'pointSize': 10,
            'title': '',
            'vAxis': {'ticks': []},
            'hAxis': {
                'ticks': [
                    {'v': (datetime.now() - timedelta(days=1)
                           ).timestamp(), 'f': _('24h ago')},
                    {'v': datetime.now().timestamp(), 'f': _('Now')}
                ]
            },
            'legend': 'none',
            'height': 90
        })

    # Graph of greatest seumers
    seum_counts_df = resets_df[['counter_trigram', 'self_seum']].copy()
    seum_counts_df['seum_count'] = np.ones(seum_counts_df.shape[0], dtype=np.float32)
    seum_counts_df = seum_counts_df.groupby(['counter_trigram']).sum().reset_index()
    # TODO: Add the ratio self_seum / seum_count
    if (seum_counts_df.shape[0] == 0):
        noBestSeum = True
        best_chart = None
    else:
        noBestSeum = False
        seum_counts_data = seum_counts_df.sort_values(by='seum_count', ascending=False)[['counter_trigram', 'seum_count']].values.tolist()
        seum_counts_data.insert(0, [_('Trigram'), _('Number of seums')])
        best_data = SimpleDataSource(seum_counts_data[:bestSeumeursNumber])
        best_chart = gchart.ColumnChart(best_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': _('Number of seums')},
            'hAxis': {'title': _('Trigram')},
        })

    # Graph of seum activity
    resets_act = resets_df[resets_df.date > (timezone.now() - timedelta(days=365))][['date']].copy()
    resets_act['year'] = resets_df.date.map(lambda d: d.year)
    resets_act['month'] = resets_df.date.map(lambda d: d.month)
    resets_act = resets_act.drop(['date'], axis=1)
    resets_act['month_counts'] = np.ones(resets_act.shape[0], dtype=int)
    resets_act = resets_act.groupby(['year', 'month']).sum().reset_index()
    if resets_act.shape[0] == 0:
        noSeumActivity = True
        activity_chart = None
    else:
        noSeumActivity = False
        seumActivity = [
            [arrow.Arrow(a[0], a[1], 1).format("MMM YYYY", locale=get_language()).capitalize(), a[2]]
            for a in resets_act.values.tolist()
        ]
        seumActivity.insert(0, [_('Month'), _('Number of seums')])
        activity_data = SimpleDataSource(seumActivity)
        activity_chart = gchart.ColumnChart(activity_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': _('Number of seums')},
            'hAxis': {'title': _('Month')},
        })

    # Graph of best likers
    best_likers_df = likes_df.drop(['liker', 'counter', 'counter_trigram'], axis=1)
    best_likers_df['count'] = np.ones(best_likers_df.shape[0], dtype=int)
    best_likers_df = best_likers_df.groupby(['liker_trigram']).sum().reset_index()
    if best_likers_df.shape[0] == 0:
        noBestLikers = True
        likers_chart = None
    else:
        noBestLikers = False
        likersCounts = best_likers_df.sort_values(by='count', ascending=False).values.tolist()
        likersCounts.insert(0, [_('Trigram'), _('Number of given likes')])
        likers_data = SimpleDataSource(likersCounts[:bestSeumeursNumber])
        likers_chart = gchart.ColumnChart(likers_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': _('Number of given likes')},
            'hAxis': {'title': _('Trigram')},
        })

    # Graph of popular hashtags
    hashtags_df['count'] = np.ones(hashtags_df.shape[0], dtype=int)
    hashtags_df = hashtags_df.groupby(['keyword']).sum().reset_index()
    hashtags_df['keyword'] = hashtags_df.keyword.map(lambda x: '#' + x)
    if hashtags_df.shape[0] == 0:
        noBestHashtags = True
        hashtags_chart = None
    else:
        noBestHashtags = False
        hashtags_data = hashtags_df.sort_values(by='count', ascending=False).values.tolist()
        hashtags_data.insert(0, [_('Hashtag'), _('Number of seums containing the hashtag')])
        hashtags_data = SimpleDataSource(hashtags_data[:bestSeumeursNumber])
        hashtags_chart = gchart.ColumnChart(hashtags_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': _('Number of seums containing the hashtag')},
            'hAxis': {'title': _('Hashtag')},
        })

    # Graph of best likee
    best_likees_df = likes_df.drop(['counter', 'liker', 'liker_trigram'], axis=1)
    best_likees_df['count'] = np.ones(best_likees_df.shape[0], dtype=int)
    best_likees_df = best_likees_df.groupby(['counter_trigram']).sum().reset_index()
    if best_likees_df.shape[0] == 0:
        noBestLikees = True
        likees_chart = None
    else:
        noBestLikees = False
        likeesCounts = best_likees_df.sort_values(by='count', ascending=False).values.tolist()
        likeesCounts.insert(0, [_('Trigram'), _('Number of received likes')])
        likees_data = SimpleDataSource(likeesCounts[:bestSeumeursNumber])
        likees_chart = gchart.ColumnChart(likees_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': _('Number of received likes')},
            'hAxis': {'title': _('Trigram')},
        })

    # At last we render the page
    return render(request, 'homeTemplate.html', {
        'counters': counters,
        'line_chart': line_chart,
        'best_chart': best_chart,
        'likers_chart': likers_chart,
        'likees_chart': likees_chart,
        'hashtags_chart': hashtags_chart,
        'activity_chart': activity_chart,
        'noTimeline': noTimeline,
        'noBestSeum': noBestSeum,
        'noBestLikers': noBestLikers,
        'noBestLikees': noBestLikees,
        'noBestHashtags': noBestHashtags,
        'noSeumActivity': noSeumActivity,
        'myCounter': myCounter,
    })


@login_required
def toggleEmailNotifications(request):
    counter = Counter.objects.get(user=request.user)
    counter.email_notifications = not counter.email_notifications
    counter.save()
    return HttpResponseRedirect(reverse('home'))


@login_required
def toggleScoreSorting(request):
    counter = Counter.objects.get(user=request.user)
    counter.sort_by_score = not counter.sort_by_score
    counter.save()
    return HttpResponseRedirect(reverse('home'))


