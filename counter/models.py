from django.db import models
from datetime import datetime
from babel.dates import format_timedelta

# Create your models here.
class Counter(models.Model):
    name = models.CharField("Nom",max_length=60)
    trigramme = models.CharField("Trigramme", max_length=3)

    def __str__(self):
        return "%s (%s)" % (self.trigramme,self.name)

    class Meta:
        verbose_name = "Compteur"

class Reset(models.Model):
    timestamp = models.DateTimeField("Date et heure",auto_now_add=True)
    reason = models.TextField("Raison")
    counter = models.ForeignKey('Counter')

    def __str__(self):
        return "%s : %s" % (self.counter,format_timedelta(datetime.now()-self.timestamp.replace(tzinfo=None),locale='fr'))

    class Meta:
        verbose_name = "Remise à zéro"
        verbose_name_plural = "Remises à zéro"
