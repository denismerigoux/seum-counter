from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _, get_language

import arrow
from babel.dates import format_timedelta


class Counter(models.Model):
    name = models.CharField(_('name'), max_length=60)
    email = models.EmailField(_('email'), max_length=264, default='null@localhost')
    trigramme = models.CharField(
        _('trigram'),
        max_length=3,
        validators=[RegexValidator(regex='^\S{3}$', message=_('Trigram must be 3 characters long.'))]
    )
    user = models.ForeignKey(User, blank=True, null=True, verbose_name=_('associated user'))
    email_notifications = models.BooleanField(_('email notifications'), default=False)
    sort_by_score = models.BooleanField(_('sort by SeumScore'), default=True)

    def __str__(self):
        return _('%(trigram)s (%(name)s)') % {'trigram': self.trigramme, 'name': self.name}

    class Meta:
        verbose_name = _('counter')

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Counter, self).save(*args, **kwargs)


class Reset(models.Model):
    timestamp = models.DateTimeField(_('datetime'), auto_now_add=True)
    reason = models.TextField(_('reason'))
    counter = models.ForeignKey('Counter', related_name='resets', verbose_name=_('victim'))
    who = models.ForeignKey('Counter', related_name='who', verbose_name=_('seum giver'), blank=True, null=True, default=None)

    def __str__(self):
        if self.who is None or self.who == self.counter:
            return _('%(counter)s: %(datetime)s (%(reason)s)') % {
                'counter': self.counter,
                'datetime': arrow.Arrow.fromdatetime(self.timestamp).humanize(locale=(get_language() or 'en')), # dirty hack...
                'reason': self.reason
            }
        else:
            return '%(who)s to %(counter)s : %(datetime)s (%(reason)s)' % {
                'who': self.who,
                'counter': self.counter,
                'datetime': arrow.Arrow.fromdatetime(self.timestamp).humanize(locale=(get_language() or 'en')),
                'reason': self.reason
            }

    class Meta:
        verbose_name = _('reset')
        verbose_name_plural = _('resets')


class Like(models.Model):
    liker = models.ForeignKey('Counter', verbose_name=_('liker'), related_name='likes')
    reset = models.ForeignKey('Reset', verbose_name=_('seum'), related_name='likes')
    timestamp = models.DateTimeField(_('datetime'), auto_now_add=True)

    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = ('liker', 'reset')

    def __str__(self):
        return _('%(liker)s likes %(reset)s') % {'liker': self.liker, 'reset': self.reset}


class Keyword(models.Model):
    text = models.CharField('texte', max_length=128, unique=True)

    class Meta:
        verbose_name = _('keyword')
        verbose_name_plural = _('keywords')

    def __str__(self):
        return '#%s' % (self.text)


class Hashtag(models.Model):
    keyword = models.ForeignKey('Keyword', verbose_name=_('hashtag'), related_name='hashtags')
    reset = models.ForeignKey('Reset', verbose_name=_('reset'), related_name='hashtags')

    class Meta:
        verbose_name = _('hashtag')
        verbose_name_plural = _('hashtags')

    def __str__(self):
        return _('%(keyword)s for %(who)s') % {'keyword': self.keyword, 'who': self.reset}
