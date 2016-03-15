from django.shortcuts import render
from counter.models import Counter,Reset
from babel.dates import format_timedelta
from datetime import datetime
from django import forms
from django.http import HttpResponseRedirect
from django.core import serializers

class resetCounterForm(forms.ModelForm):
    class Meta:
        model = Reset
        fields = ['reason','counter']

# Create your views here.
def home(request):
    #Display counters
    counters = Counter.objects.all()
    for counter in counters:
        lastReset = Reset.objects.filter(counter=counter).order_by('-timestamp')
        if (lastReset.count() == 0):
            counter.lastReset = False
        else:
            counter.lastReset = lastReset[0]
            counter.lastReset.delta = datetime.now()-counter.lastReset.timestamp.replace(tzinfo=None)
            counter.lastReset.formatted_delta = format_timedelta(counter.lastReset.delta,locale='fr')
        counter.isHidden = "hidden"
    return render(request,'counterTemplate.html', {'counters' : counters})

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
