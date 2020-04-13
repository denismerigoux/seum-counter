from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from counter.models import Counter


def create(request):
    if (request.method == 'POST'):
        # create a form instance and populate it with data from the request:
        data = dict(request.POST)
        email = data['email'][0]
        username = email.split('@')[0]
        trigramme = data['trigramme'][0]
        nick = data['nick'][0]
        password1 = data['password1'][0]
        password2 = data['password2'][0]
        email_notifications = 'email_notifications' in data.keys()

        if len(trigramme) != 3:
            error = _("Trigram must be 3 characters long.")
            return render(request, 'createUser.html', {'error': error})

        if password1 != password2:
            error = _("Passwords do not match.")
            return render(request, 'createUser.html', {'error': error})

        try:
            test_user = User.objects.get(email=email)
            error = _("A user with this email address already exists.")
            return render(request, 'createUser.html', {'error': error})
        except User.DoesNotExist:
            try:
                user = User.objects.create_user(username, email, password1)
            except IntegrityError:
                error = _("Use another email address, another user has already this login.")
                return render(request, 'createUser.html', {'error': error})

            counter = Counter.objects.create(name=nick, email=email, trigramme=trigramme, user=user, email_notifications=email_notifications)
            return render(request, 'createUserDone.html', {'login': username})
    else:
        return render(request, 'createUser.html', {'error': None})
