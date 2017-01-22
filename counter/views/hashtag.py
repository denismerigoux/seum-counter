from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _, get_language

import arrow
from babel.dates import format_timedelta, format_datetime

from counter.models import *


@login_required
def get(request, keyword):
    try:
        keyword = Keyword.objects.get(text=keyword)
    except Keyword.DoesNotExist:
        print('erreur !')
        return HttpResponseRedirect(reverse('home'))

    hashtag = '#' + keyword.text
    resets = Reset.objects.prefetch_related('likes', 'who', 'counter').filter(hashtags__keyword=keyword).order_by('-timestamp')
    totalNumber = resets.count()
    cur_lang = get_language()

    for reset in resets:
        if reset.who is None or reset.who == reset.counter:
            reset.selfSeum = True
        else:
            reset.selfSeum = False
        reset.likeCount = reset.likes.count()
    return render(request, 'hashtagTemplate.html', {
        'hashtag': hashtag,
        'totalNumber': totalNumber,
        'resets': resets,
    })
