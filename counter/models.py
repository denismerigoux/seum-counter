from django.db import models
from datetime import datetime
from babel.dates import format_timedelta

# Create your models here.
class Counter(models.Model):
    name=models.CharField("Nom",max_length=60)
    lastReset=models.DateTimeField("Dernière remise à zéro")

    def __str__(self):
        return "%s : %s" % (self.name,format_timedelta(datetime.now()-self.lastReset.replace(tzinfo=None),locale='fr'))

    class Meta:
        verbose_name = "Compteur"
