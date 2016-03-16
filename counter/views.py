from django.shortcuts import render
from counter.models import Counter,Reset
from babel.dates import format_timedelta
from datetime import datetime,timedelta
from django import forms
from django.http import HttpResponseRedirect
from django.core import serializers
from graphos.renderers import gchart
from graphos.sources.simple import SimpleDataSource

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
            lastResets.append([counter.trigramme,(counter.lastReset.delta.total_seconds())/(24*3600)])
            if (counter.lastReset.delta.total_seconds())/(24*3600) > maxJSS:
                maxJSS = (counter.lastReset.delta.total_seconds())/(24*3600)
            counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta,locale='fr',threshold=1)
        counter.isHidden = "hidden"
    counters = sorted(counters,key=lambda t: -t.lastReset.delta)
    #Generate graph
    lastResets.sort(key=lambda x: (x[1],x[0]))
    lastResets.insert(0,['Trigramme','Jours sans seum'])
    data = SimpleDataSource(lastResets)
    chart = gchart.ColumnChart(data,options={'title' : '', 'legend' : 'none','vAxis' : { 'viewWindow' : { 'max' : max(maxJSS,1) , 'min' : 0} , 'ticks' : [1,2,3,4,5,6,7,8,9,10,11,12,13,14],'title' : 'Jours sans seum' }, 'hAxis' : {'title' : 'Trigramme' }})
    return render(request,'homeTemplate.html', {'counters' : counters, 'chart' : chart})

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
    return HttpResponseRedirect('/')

def counter(request, id_counter):
    counter = Counter.objects.get(pk=id_counter)
    lastReset = Reset.objects.filter(counter=counter).order_by('-timestamp')
    if (lastReset.count() == 0):
        counter.lastReset = Reset()
        counter.lastReset.delta = timezero
        counter.lastReset.noSeum = True
    else:
        counter.lastReset = lastReset[0]
        counter.lastReset.noSeum = False
        counter.lastReset.delta = datetime.now()-counter.lastReset.timestamp.replace(tzinfo=None)

    return render(request,'counterTemplate.html', { 'counter' : counter})
