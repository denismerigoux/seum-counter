from django.shortcuts import render
from counter.models import Counter, Reset
from babel.dates import format_timedelta, format_datetime
from datetime import datetime, timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.core import serializers
from django.core.mail import EmailMessage
from graphos.renderers import gchart
from graphos.sources.simple import SimpleDataSource
from graphos.sources.model import ModelDataSource
import random
import math
from django.utils import timezone


class resetCounterForm(forms.ModelForm):

    class Meta:
        model = Reset
        fields = ['reason', 'counter']


def home(request):
    # JSS above this limit will not be displayed on the col graph
    JSS_limit = 7
    maxJSS = 0
    bestSeumeursNumber = 15
    # Display counters
    counters = Counter.objects.all()
    lastResets = []
    # Calculates infos for each counter
    timezero = timedelta(0)
    for counter in counters:
        lastReset = Reset.objects.filter(
            counter=counter).order_by('-timestamp')
        if (lastReset.count() == 0):
            # This person never had the seum
            counter.lastReset = Reset()
            counter.lastReset.delta = timezero
            counter.lastReset.noSeum = True
            counter.CSSclass = "warning"
        else:
            counter.lastReset = lastReset[0]
            counter.lastReset.noSeum = False
            counter.lastReset.delta = datetime.now(
            ) - counter.lastReset.timestamp.replace(tzinfo=None)
            if ((counter.lastReset.delta.total_seconds()) / (24 * 3600) <
                    JSS_limit):
                # Less than 7 JSS -> display on graph
                lastResets.append(
                    [counter.trigramme,
                     {'v': (counter.lastReset.delta.total_seconds()) /
                      (24 * 3600),
                      'f': str(round(
                          (counter.lastReset.delta.total_seconds()) /
                          (24 * 3600), 1))}])
                # Updating the max JSS displayed on the graph to compute scale
                if (counter.lastReset.delta.total_seconds() / (24 * 3600) >
                        maxJSS):
                    maxJSS = (counter.lastReset.delta.total_seconds() /
                              (24 * 3600))
            # Defining CSS attributes for the counter
            counter.CSSclass = "primary"
            counter.opacity = 0.3 + 0.7 * \
                math.exp(-(counter.lastReset.delta.total_seconds()) /
                         (7 * 24 * 3600))
            # Computing the total number of resets for this counter
            counter.seumCount = Reset.objects.filter(
                counter=counter).count()
        counter.lastReset.formatted_delta = format_timedelta(
            counter.lastReset.delta, locale='fr', threshold=1)
        counter.isHidden = "hidden"
    counters = sorted(counters, key=lambda t: t.lastReset.delta)
    # Column graph
    if (len(lastResets) == 0):
        noGraph = True
        col_chart = None
    else:
        noGraph = False
        lastResets.sort(key=lambda x: x[1]['v'])
        lastResets.insert(0, ['Trigramme', 'Jours sans seum'])
        col_data = SimpleDataSource(lastResets)
        col_chart = gchart.ColumnChart(col_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {
                'viewWindow': {
                    'max': max(maxJSS, 1),
                    'min': 0
                },
                'ticks': [1, 2, 3, 4, 5, 6, 7],
                'title': 'Jours sans seum'
            },
            'hAxis': {'title': 'Trigramme'},
        })

    # Timeline graph
    # Data pre-processing
    resets = Reset.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=1))
    if (resets.count() == 0):
        noTimeline = True
        line_chart = None
    else:
        noTimeline = False
        for reset in resets:
            reset.timestamp = {
                'v': reset.timestamp.timestamp(),
                'f': "Il y a " + format_timedelta(datetime.now() -
                                                  reset.timestamp.replace(
                                                      tzinfo=None),
                                                  locale='fr', threshold=1)
            }
            reset.Seum = {
                'v': 0, 'f': reset.counter.trigramme + " : " + reset.reason}
        # Drawing the graph
        line_data = ModelDataSource(resets, fields=['timestamp', 'Seum'])
        line_chart = gchart.LineChart(line_data, options={
            'lineWidth': 0,
            'pointSize': 10,
            'title': '',
            'vAxis': {'ticks': []},
            'hAxis': {
                'ticks': [
                    {'v': (datetime.now() - timedelta(days=1)
                           ).timestamp(), 'f': 'Il y a 24 h'},
                    {'v': datetime.now().timestamp(), 'f': 'Présent'}
                ]
            },
            'legend': 'none',
            'height': 90
        })
    # Graph of greatest seumers
    seumCounts = []
    for counter in counters:
        seumCounts.append([counter.trigramme, Reset.objects.filter(
            counter=counter).count()])
    if (len(seumCounts) == 0):
        noBestSeum = True
        best_chart = None
    else:
        seumCounts.sort(key=lambda x: -x[1])
        noBestSeum = False
        seumCounts.insert(0, ['Trigramme', 'Nombre de seums'])
        best_data = SimpleDataSource(seumCounts[:bestSeumeursNumber])
        best_chart = gchart.ColumnChart(best_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': 'Nombre de seums'},
            'hAxis': {'title': 'Trigramme'},
        })

    return render(request, 'homeTemplate.html', {
        'counters': counters,
        'col_chart': col_chart,
        'line_chart': line_chart,
        'best_chart': best_chart,
        'noTimeline': noTimeline,
        'noGraph': noGraph,
        'noBestSeum': noBestSeum
    })


def resetCounter(request):
    # Update Form counter
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        counter = Counter.objects.get(pk=int(data['counter'][0]))
        reset = Reset()
        reset.counter = counter
        reset.reason = data['reason'][0]
        reset.timestamp = datetime.now()
        reset.save()
        # We send the emails only to those who have an email address
        emails = [u[0] for u in Counter.objects.all().values_list('email')
                  if u[0] != 'null@localhost']
        # Now send emails to everyone
        email_to_send = EmailMessage(counter.name + ' a le seum',
                                     data['reason'][0] + '''

--
SeumBook™ - http://seum.merigoux.ovh

P.S. : Pour ne plus recevoir ces messages, envoie un mail à denis.merigoux@gmail.com''',
                                     'SeumMan <seum@merigoux.ovh>', emails, [],
                                     reply_to=emails)
    email_to_send.send()

    return HttpResponseRedirect(data['redirect'][0])


def counter(request, id_counter):

    counter = Counter.objects.get(pk=id_counter)
    resets = Reset.objects.filter(counter=counter).order_by('-timestamp')
    timezero = timedelta(0)
    # Display
    if (resets.count() == 0):
        counter.lastReset = Reset()
        counter.lastReset.delta = timezero
        counter.lastReset.noSeum = True
    else:
        counter.lastReset = resets[0]
        counter.lastReset.noSeum = False
        counter.lastReset.delta = datetime.now(
        ) - counter.lastReset.timestamp.replace(tzinfo=None)
        counter.lastReset.formatted_delta = format_timedelta(
            counter.lastReset.delta, locale='fr', threshold=1)
        counter.seumCount = Reset.objects.filter(
            counter=counter).count()

    for reset in resets:
        reset.date = format_datetime(
            reset.timestamp, locale='fr',
            format="EEEE dd MMMM Y 'à' HH:mm:ss").capitalize()
    # Timeline graph
    # Data pre-processing
    resets_graph = resets
    for reset in resets_graph:
        reset.timestamp = {
            'v': reset.timestamp.timestamp(),
            'f': "Il y a " + format_timedelta(
                datetime.now() - reset.timestamp.replace(tzinfo=None),
                locale='fr', threshold=1)
        }
        reset.Seum = {'v': 0, 'f': reset.reason}
    # Drawing the graph
    data = ModelDataSource(resets, fields=['timestamp', 'Seum'])
    chart = gchart.LineChart(data, options={
        'lineWidth': 0,
        'pointSize': 10,
        'title': '',
        'vAxis': {'ticks': []},
        'hAxis': {'ticks': [{
            'v': datetime(2016, 3, 9, 23, 0, 0, 0).timestamp(),
            'f': 'ADD des X2013'
        }, {
            'v': datetime.now().timestamp(),
            'f': 'Présent'}
        ]},
        'legend': 'none',
        'height': 90
    })

    return render(request, 'counterTemplate.html', {'counter': counter, 'chart': chart, 'resets': resets})
