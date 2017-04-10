from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from counter.models import *


@login_required
def like(request):
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        liker = Counter.objects.get(pk=data['liker'][0])
        reset = Reset.objects.get(pk=data['reset'][0])
        like = Like.objects.create(liker=liker, reset=reset)
    return HttpResponseRedirect(data['redirect'][0])
