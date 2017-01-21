from datetime import datetime, timedelta
import copy

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _, get_language

import arrow
from babel.dates import format_timedelta, format_datetime
from graphos.renderers import gchart
from graphos.sources.model import ModelDataSource

from counter.models import *


@login_required
def get(request, id_counter):
    try:
        myCounter = Counter.objects.get(user__id=request.user.id)
    except Counter.DoesNotExist:
        return HttpResponseRedirect(reverse('login'))

    counter = Counter.objects.prefetch_related('resets', 'resets__likes').get(pk=id_counter)
    resets = counter.resets.order_by('-timestamp')
    timezero = timedelta(0)

    # Display
    if resets.count() == 0:
        counter.lastReset = Reset()
        counter.lastReset.delta = timezero
        counter.lastReset.noSeum = True
        seumFrequency = _('unknown')
    else:
        firstReset = resets.reverse()[0]
        counter.lastReset = resets[0]
        counter.lastReset.noSeum = False
        if counter.lastReset.who is None or counter.lastReset.who == counter:
            counter.lastReset.selfSeum = True
        else:
            counter.lastReset.selfSeum = False

        counter.lastReset.formatted_delta = arrow.Arrow.fromdatetime(counter.lastReset.timestamp).humanize(locale=get_language())
        counter.seumCount = counter.resets.count()
        seumFrequency = format_timedelta((datetime.now() - firstReset.timestamp.replace(tzinfo=None)) / counter.seumCount,
            locale=get_language(), threshold=1)

        counter.lastLikes = list(counter.lastReset.likes.all())
        counter.alreadyLiked = myCounter.id in [l.liker.id for l in counter.lastLikes]
        counter.likeCount = len(counter.lastLikes)
        if counter.likeCount > 0:
            counter.likersString = ", ".join(like.liker.trigramme for like in counter.lastLikes)

    for reset in resets:
        if reset.who is None or reset.who == reset.counter:
            reset.selfSeum = True
        else:
            reset.selfSeum = False
        reset.date = reset.timestamp
        reset.likeCount = reset.likes.count()

    # Timeline graph
    # Data pre-processing
    if not counter.lastReset.noSeum:
        resets_graph = resets
        for reset in resets_graph:
            reset.timestamp = {
                'v': reset.timestamp.timestamp(),
                'f': arrow.Arrow.fromdatetime(reset.timestamp).humanize(locale=get_language())
            }
            if reset.selfSeum:
                reset.Seum = {'v': 0, 'f': reset.reason}
            else:
                reset.Seum = {'v': 0, 'f': _('From %(who)s: %(reason)s') % {'who': reset.who.trigramme, 'reason': reset.reason}}

        # Drawing the graph
        data = ModelDataSource(resets, fields=['timestamp', 'Seum'])
        chart = gchart.LineChart(data, options={
            'lineWidth': 0,
            'pointSize': 10,
            'title': '',
            'vAxis': {'ticks': []},
            'hAxis': {'ticks': [{
                'v': firstReset.timestamp.timestamp(),
                'f': arrow.Arrow.fromdatetime(firstReset.timestamp).humanize(locale=get_language())
            }, {
                'v': datetime.now().timestamp(),
                'f': 'Présent'}
            ]},
            'legend': 'none',
            'height': 90
        })
    else:
        chart = None

    return render(request, 'counterTemplate.html', {
        'counter': counter,
        'chart': chart,
        'resets': resets,
        'seumFrequency': seumFrequency,
        'myCounter': myCounter,
    })
