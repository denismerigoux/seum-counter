from django.db import models
from datetime import datetime
from babel.dates import format_timedelta
from django.contrib.auth.models import User

# Create your models here.


class Counter(models.Model):
    name = models.CharField("Nom", max_length=60)
    email = models.EmailField("Email", max_length=264,
                              default="null@localhost")
    trigramme = models.CharField("Trigramme", max_length=3)
    user = models.ForeignKey(User, blank=True, null=True)
    email_notifications = models.BooleanField(
        "Notifications par email", default=False)

    def __str__(self):
        return "%s (%s)" % (self.trigramme, self.name)

    class Meta:
        verbose_name = "Compteur"


class Reset(models.Model):
    timestamp = models.DateTimeField("Date et heure", auto_now_add=True)
    reason = models.TextField("Raison")
    counter = models.ForeignKey('Counter', related_name='counter')
    who = models.ForeignKey('Counter', related_name='who',
                            blank=True, null=True, default=None)

    def __str__(self):
        return "%s : %s (%s)" % (self.counter,
                                 format_timedelta(
                                     datetime.now() -
                                     self.timestamp.replace(tzinfo=None),
                                     locale='fr'), self.reason)

    class Meta:
        verbose_name = "Remise à zéro"
        verbose_name_plural = "Remises à zéro"
