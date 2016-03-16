from django.shortcuts import render
from counter.models import Counter,Reset
from babel.dates import format_timedelta
from datetime import datetime,timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.core import serializers
from graphos.renderers import gchart
from graphos.sources.simple import SimpleDataSource
from graphos.sources.model import ModelDataSource
import random

class resetCounterForm(forms.ModelForm):
    class Meta:
        model = Reset
        fields = ['reason','counter']

# Create your views here.
def home(request):
    #Display counters
    counters = Counter.objects.all()
    lastResets = []
    #Calculates infos for each counter
    maxJSS = 0
    timezero = timedelta(0)
    for counter in counters:
        lastReset = Reset.objects.filter(counter=counter).order_by('-timestamp')
        if (lastReset.count() == 0):
            counter.lastReset = Reset()
            counter.lastReset.delta = timezero
            counter.lastReset.noSeum = True
        else:
            counter.lastReset = lastReset[0]
            counter.lastReset.noSeum = False
            counter.lastReset.delta = datetime.now()-counter.lastReset.timestamp.replace(tzinfo=None)
            lastResets.append([counter.trigramme,{'v' : (counter.lastReset.delta.total_seconds())/(24*3600), 'f' : str(round((counter.lastReset.delta.total_seconds())/(24*3600),1))} ])
            if (counter.lastReset.delta.total_seconds())/(24*3600) > maxJSS:
                maxJSS = (counter.lastReset.delta.total_seconds())/(24*3600)
            counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta,locale='fr',threshold=1)
        counter.isHidden = "hidden"
    counters = sorted(counters,key=lambda t: -t.lastReset.delta)
    #Column graph
    lastResets.sort(key=lambda x: x[1]['v'])
    lastResets.insert(0,['Trigramme','Jours sans seum'])
    col_data = SimpleDataSource(lastResets)
    col_chart = gchart.ColumnChart(col_data,options={'title' : '', 'legend' : 'none','vAxis' : { 'viewWindow' : { 'max' : max(maxJSS,1) , 'min' : 0} , 'ticks' : [1,2,3,4,5,6,7,8,9,10,11,12,13,14],'title' : 'Jours sans seum' }, 'hAxis' : {'title' : 'Trigramme' }})

    ###Timeline graph
    #Data pre-processing
    resets = Reset.objects.filter(timestamp__gte=datetime.now() - timedelta(days=1))
    for reset in resets:
        reset.timestamp={'v' : reset.timestamp.timestamp(), 'f' : "Il y a "+format_timedelta(datetime.now()-reset.timestamp.replace(tzinfo=None),locale='fr',threshold=1) }
        reset.Seum={'v' : 0, 'f' : reset.counter.trigramme+" : "+reset.reason}
    #Drawing the graph
    line_data = ModelDataSource(resets,fields=['timestamp','Seum'])
    line_chart = gchart.LineChart(line_data, options={
        'lineWidth' : 0,
        'pointSize' : 10,
        'title' : '',
        'vAxis' : { 'ticks' : []},
        'hAxis' : {'ticks' : [{'v' : (datetime.now() - timedelta(days=1)).timestamp(), 'f' : 'Il y a 24 h' }, { 'v' :datetime.now().timestamp(), 'f' : 'Présent'}]},
        'legend' : 'none',
        'height' : 90
    })

    return render(request,'homeTemplate.html', {'counters' : counters, 'col_chart' : col_chart, 'line_chart' : line_chart})

def resetCounter(request):
    #Update Form counter
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        counter =  Counter.objects.get(pk=int(data['counter'][0]))
        reset = Reset()
        reset.counter = counter
        reset.reason = data['reason'][0]
        reset.timestamp = datetime.now()
        reset.save()
        # check whether it's valid
    return HttpResponseRedirect('/'+data['redirect'][0])

def counter(request, id_counter):

    counter = Counter.objects.get(pk=id_counter)
    resets = Reset.objects.filter(counter=counter)
    lastReset = resets.order_by('-timestamp')
    #Display
    if (lastReset.count() == 0):
        counter.lastReset = Reset()
        counter.lastReset.delta = timezero
        counter.lastReset.noSeum = True
    else:
        counter.lastReset = lastReset[0]
        counter.lastReset.noSeum = False
        counter.lastReset.delta = datetime.now()-counter.lastReset.timestamp.replace(tzinfo=None)
        counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta,locale='fr',threshold=1)

    ###Timeline graph
    #Data pre-processing
    for reset in resets:
        reset.timestamp={'v' : reset.timestamp.timestamp(), 'f' : "Il y a "+format_timedelta(datetime.now()-reset.timestamp.replace(tzinfo=None),locale='fr',threshold=1) }
        reset.Seum={'v' : 0, 'f' : reset.reason}
    #Drawing the graph
    data = ModelDataSource(resets,fields=['timestamp','Seum'])
    chart = gchart.LineChart(data, options={
        'lineWidth' : 0,
        'pointSize' : 10,
        'title' : '',
        'vAxis' : { 'ticks' : []},
        'hAxis' : {'ticks' : [{'v' : datetime(2016,3,9,23,0,0,0).timestamp(), 'f' : 'ADD des X2013' }, { 'v' :datetime.now().timestamp(), 'f' : 'Présent'}]},
        'legend' : 'none',
        'height' : 90
    })

    return render(request,'counterTemplate.html', { 'counter' : counter, 'chart' : chart})
