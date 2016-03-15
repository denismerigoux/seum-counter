from django.shortcuts import render
from counter.models import Counter,Reset
from babel.dates import format_timedelta
from datetime import datetime
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
    lastResets = [['Trigramme','Jours sans seum']]
    #Calculates infos for each counter
    maxJSS = 0
    for counter in counters:
        lastReset = Reset.objects.filter(counter=counter).order_by('-timestamp')
        if (lastReset.count() == 0):
            counter.lastReset = False
        else:
            counter.lastReset = lastReset[0]
            counter.lastReset.delta = datetime.now()-counter.lastReset.timestamp.replace(tzinfo=None)
            lastResets.append([counter.trigramme,(counter.lastReset.delta.total_seconds())/(24*3600)])
            if (counter.lastReset.delta.total_seconds())/(24*3600) > maxJSS:
                maxJSS = (counter.lastReset.delta.total_seconds())/(24*3600)
            counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta,locale='fr')
        counter.isHidden = "hidden"

    #Generate graph
    data = SimpleDataSource(lastResets)
    chart = gchart.ColumnChart(data,options={'title' : 'Graphe du seum', 'legend' : 'none','vAxis' : { 'viewWindow' : { 'max' : max(maxJSS,1) , 'min' : 0} , 'ticks' : [1,2,3,4,5,6,7,8,9,10,11,12,13,14],'title' : 'Jours sans seum' }, 'hAxis' : {'title' : 'Trigramme' }})
    return render(request,'counterTemplate.html', {'counters' : counters, 'chart' : chart})

def resetCounter(request):
    #Update Form counter
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        counter =  Counter.objects.get(pk=int(data['counter'][0]))
        print(counter)
        reset = Reset()
        reset.counter = counter
        reset.reason = data['reason'][0]
        reset.timestamp = datetime.now()
        reset.save()
        # check whether it's valid
    return HttpResponseRedirect('/')
