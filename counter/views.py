from django.shortcuts import render
from counter.models import Counter, Reset
from django.contrib.auth.models import User
from babel.dates import format_timedelta, format_datetime
from datetime import datetime, timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from graphos.renderers import gchart
from django.template.loader import render_to_string
from graphos.sources.simple import SimpleDataSource
from graphos.sources.model import ModelDataSource
import random
import math
import copy
from django.utils import timezone


@login_required
def home(request):
    # JSS above this limit will not be displayed on the col graph
    JSS_limit = 7
    maxJSS = 0
    bestSeumeursNumber = 15
    lastResets = []
    no_seum_delta = timedelta.max

    # First select our counter
    try:
        myCounter = Counter.objects.get(user__id=request.user.id)
        lastReset = Reset.objects.filter(
            counter=myCounter).order_by('-timestamp')
        if (lastReset.count() == 0):
            # This person never had the seum
            myCounter.lastReset = Reset()
            myCounter.lastReset.delta = no_seum_delta
            myCounter.lastReset.noSeum = True
        else:
            myCounter.lastReset = lastReset[0]
            myCounter.lastReset.noSeum = False
            if (myCounter.lastReset.who is None or
                    myCounter.lastReset.who.id == myCounter.id):
                myCounter.lastReset.selfSeum = True
            else:
                myCounter.lastReset.selfSeum = False
            myCounter.lastReset.delta = datetime.now(
            ) - myCounter.lastReset.timestamp.replace(tzinfo=None)
            myCounter.seumCount = Reset.objects.filter(
                counter=myCounter).count()
        myCounter.lastReset.formatted_delta = format_timedelta(
            myCounter.lastReset.delta, locale='fr', threshold=1)
    except Counter.DoesNotExist:
        return HttpResponseRedirect(reverse('login'))

    # Building data for counters display
    counters = Counter.objects.all()
    for counter in counters:
        lastReset = Reset.objects.filter(
            counter=counter).order_by('-timestamp')
        if (lastReset.count() == 0):
            # This person never had the seum
            counter.lastReset = Reset()
            counter.lastReset.delta = no_seum_delta
            counter.lastReset.noSeum = True
            counter.CSSclass = "warning"
        else:
            counter.lastReset = lastReset[0]
            if (counter.lastReset.who is None or
                    counter.lastReset.who.id == counter.id):
                counter.lastReset.selfSeum = True
            else:
                counter.lastReset.selfSeum = False
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
            counter.CSSclass = "default"
            counter.opacity = 0.4 + 0.6 * \
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
            if (reset.who is None or
                    reset.who.id == reset.counter.id):
                reset.Seum = {'v': 0,
                              'f': reset.counter.trigramme +
                              " : " + reset.reason}
            else:
                reset.Seum = {'v': 0,
                              'f': reset.who.trigramme + ' à ' +
                              reset.counter.trigramme +
                              " : " + reset.reason}
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

    # Graph of seum activity
    resets = Reset.objects.filter(
        timestamp__gte=timezone.now() - timedelta(days=365))
    months = {}
    for reset in resets:
        monthDate = datetime(reset.timestamp.year, reset.timestamp.month, 1)
        months[monthDate] = months.get(monthDate, 0) + 1

    monthList = sorted(months.items(), key=lambda t: t[0])
    seumActivity = []
    for month in monthList:
        seumActivity.append(
            [format_datetime(month[0], locale='fr',
                             format="MMM Y").capitalize(), month[1]])
    if (len(seumActivity) == 0):
        noSeumActivity = True
        activity_chart = None
    else:
        noSeumActivity = False
        seumActivity.insert(0, ['Mois', 'Nombre de seums'])
        activity_data = SimpleDataSource(seumActivity)
        activity_chart = gchart.ColumnChart(activity_data, options={
            'title': '',
            'legend': 'none',
            'vAxis': {'title': 'Nombre de seums'},
            'hAxis': {'title': 'Mois'},
        })

    return render(request, 'homeTemplate.html', {
        'counters': counters,
        'col_chart': col_chart,
        'line_chart': line_chart,
        'best_chart': best_chart,
        'activity_chart': activity_chart,
        'noTimeline': noTimeline,
        'noGraph': noGraph,
        'noBestSeum': noBestSeum,
        'noSeumActivity': noSeumActivity,
        'myCounter': myCounter,
    })


@login_required
def resetCounter(request):
    # Update Form counter
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)

        who = Counter.objects.get(pk=int(data['who'][0]))
        if 'counter' in data.keys():
            counter = Counter.objects.get(pk=int(data['counter'][0]))
        else:
            try:
                counter = Counter.objects.get(trigramme=data['trigramme'][0])
            except Counter.DoesNotExist:
                return HttpResponseRedirect(data['redirect'][0])
        reset = Reset()
        reset.counter = counter
        reset.who = who
        reset.reason = data['reason'][0]
        reset.timestamp = datetime.now()

        # we check that the seumer is the autenticated user
        if (reset.who.user is None or
                reset.who.user.id != request.user.id):
            return HttpResponseRedirect(data['redirect'][0])

        reset.save()
        # We send the emails only to those who want
        emails = [u.email for u in Counter.objects.all()
                  if u.email_notifications]
        # Now send emails to everyone
        if (reset.who is None or
                reset.who.id == counter.id):
            selfSeum = True
        else:
            selfSeum = False
        text_of_email = render_to_string(
            'seumEmail.txt', {'reason': data['reason'][0],
                              'name': counter.name,
                              'who': reset.who,
                              'selfSeum': selfSeum,
                              })
        email_to_send = EmailMessage(
            '[SeumBook] ' + counter.trigramme + ' a le seum',
            text_of_email,
            'SeumMan <seum@merigoux.ovh>', emails, [],
            reply_to=emails)
        email_to_send.send(fail_silently=True)

    return HttpResponseRedirect(data['redirect'][0])


@login_required
def counter(request, id_counter):

    try:
        myCounter = Counter.objects.get(user__id=request.user.id)
    except Counter.DoesNotExist:
        return HttpResponseRedirect(reverse('login'))

    counter = Counter.objects.get(pk=id_counter)
    resets = Reset.objects.filter(counter=counter).order_by('-timestamp')
    timezero = timedelta(0)
    # Display
    if (resets.count() == 0):
        counter.lastReset = Reset()
        counter.lastReset.delta = timezero
        counter.lastReset.noSeum = True
        seumFrequency = 'inconnu'
    else:
        firstReset = copy.copy(resets[len(resets) - 1])
        counter.lastReset = resets[0]
        counter.lastReset.noSeum = False
        if (counter.lastReset.who is None or
                counter.lastReset.who.id == counter.id):
            counter.lastReset.selfSeum = True
        else:
            counter.lastReset.selfSeum = False
        counter.lastReset.delta = datetime.now(
        ) - counter.lastReset.timestamp.replace(tzinfo=None)
        counter.lastReset.formatted_delta = format_timedelta(
            counter.lastReset.delta, locale='fr', threshold=1)
        counter.seumCount = Reset.objects.filter(
            counter=counter).count()
        seumFrequency = format_timedelta((
            datetime.now() - firstReset.timestamp.replace(tzinfo=None)) /
            counter.seumCount, locale='fr', threshold=1)

    for reset in resets:
        if (reset.who is None or
                reset.who.id == reset.counter.id):
            reset.selfSeum = True
        else:
            reset.selfSeum = False
        reset.date = format_datetime(
            reset.timestamp, locale='fr',
            format="dd/MM/Y HH:mm")
    # Timeline graph
    # Data pre-processing
    if not counter.lastReset.noSeum:
        resets_graph = resets
        for reset in resets_graph:
            reset.timestamp = {
                'v': reset.timestamp.timestamp(),
                'f': "Il y a " + format_timedelta(
                    datetime.now() - reset.timestamp.replace(tzinfo=None),
                    locale='fr', threshold=1)
            }
            if reset.selfSeum:
                reset.Seum = {'v': 0, 'f': reset.reason}
            else:
                reset.Seum = {'v': 0, 'f': 'De ' + reset.who.trigramme + ' : ' +
                              reset.reason}
        # Drawing the graph
        data = ModelDataSource(
            resets, fields=['timestamp', 'Seum'])
        chart = gchart.LineChart(data, options={
            'lineWidth': 0,
            'pointSize': 10,
            'title': '',
            'vAxis': {'ticks': []},
            'hAxis': {'ticks': [{
                'v': firstReset.timestamp.timestamp(),
                'f': 'Il y a ' + format_timedelta(
                    datetime.now() - firstReset.timestamp.replace(tzinfo=None),
                    locale='fr', threshold=1)
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


def createUser(request):
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        email = data['email'][0]
        username = email.split('@')[0]
        trigramme = data['trigramme'][0]
        nick = data['nick'][0]
        password1 = data['password1'][0]
        password2 = data['password2'][0]
        email_notifications = ('email_notifications' in data.keys())

        if password1 != password2:
            error = "Les deux mots de passe sont différents."
            return render(request, 'createUser.html', {'error': error})
        try:
            test_user = User.objects.get(email=email)
            error = "Un utilisateur avec cette adresse email existe déjà !"
            return render(request, 'createUser.html', {'error': error})
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(username, email, password1)
            except IntegrityError:
                error = "Utilise une autre adresse email, un autre utilisateur \
                 a le même login que toi."
                return render(request, 'createUser.html', {'error': error})
            counter = Counter()
            counter.name = nick
            counter.email = email
            counter.trigramme = trigramme
            counter.user = user
            counter.email_notifications = False
            counter.save()
            return render(request, 'createUserDone.html', {'login': username})
    else:
        return render(request, 'createUser.html', {'error': None})


@login_required
def toggleEmailNotifications(request):
    counter = Counter.objects.get(user=request.user)
    counter.email_notifications = not counter.email_notifications
    counter.save()
    return HttpResponseRedirect(reverse('home'))
