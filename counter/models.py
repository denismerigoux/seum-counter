from django.db import models
from datetime import datetime
from babel.dates import format_timedelta
from django.contrib.auth.models import User

# Create your models here.


class Counter(models.Model):
    name = models.CharField('nom', max_length=60)
    email = models.EmailField('email', max_length=264,
                              default='null@localhost')
    trigramme = models.CharField('trigramme', max_length=3)
    user = models.ForeignKey(User, blank=True, null=True,
                             verbose_name='utilisateur associé')
    email_notifications = models.BooleanField(
        'notifications par email', default=False)
    sort_by_score = models.BooleanField(
        'trier par SeumScore™', default=True)

    def __str__(self):
        return '%s (%s)' % (self.trigramme, self.name)

    class Meta:
        verbose_name = 'compteur'


class Reset(models.Model):
    timestamp = models.DateTimeField('date et heure', auto_now_add=True)
    reason = models.TextField('raison')
    counter = models.ForeignKey('Counter', related_name='counter',
                                verbose_name='victime')
    who = models.ForeignKey('Counter', related_name='who',
                            verbose_name='fouteur de seum',
                            blank=True, null=True, default=None)

    def __str__(self):
        if (self.who is None or
                self.who.id == self.counter.id):
            return '%s : %s (%s)' % (self.counter,
                                     format_timedelta(
                                         datetime.now() -
                                         self.timestamp.replace(tzinfo=None),
                                         locale='fr'), self.reason)
        else:
            return '%s à %s : %s (%s)' % (self.who, self.counter,
                                          format_timedelta(
                                              datetime.now() -
                                              self.timestamp.replace(
                                                  tzinfo=None),
                                              locale='fr'), self.reason)

    class Meta:
        verbose_name = 'remise à zéro'
        verbose_name_plural = 'remises à zéro'


class Like(models.Model):
    liker = models.ForeignKey('Counter', verbose_name='likeur')
    reset = models.ForeignKey('Reset', verbose_name='seum')
    timestamp = models.DateTimeField('date et heure', auto_now_add=True)

    class Meta:
        verbose_name = 'like'
        verbose_name_plural = 'likes'
        unique_together = ('liker', 'reset')

    def __str__(self):
        return '%s aime %s' % (self.liker, self.reset)
