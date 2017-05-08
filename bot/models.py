from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _, get_language

import arrow
from babel.dates import format_timedelta

# Link a SeumBook counter to a Telegram User
class TelegramUser(models.Model):
    counter = models.ForeignKey('counter.Counter', verbose_name=_('counter'))
    telegram_user_id = models.BigIntegerField(_('telegram_user_id'), unique=True)

    class Meta:
        verbose_name = _('telegram_user')
        verbose_name_plural = _('telegram_users')

    def __str__(self):
        return _('%(counter)s is %(telegram_user_id)d') % {'counter': self.counter, 'telegram_user_id': self.telegram_user_id}

# When a user wants to link his SeumBook account to his Telegram account,
# he/she send a message to the bot in a private chat, then the bot answers with
# an URL to the SeumBook website containing a `verif_key`. The user then log in
# on the SeumBook website, and based on the `verif_key` parameter, we find the
# corresponding Telegram User.
# This object remember which Telegram User received which `verif_key`
class TelegramUserCheck(models.Model):
    telegram_user_id = models.BigIntegerField(_('telegram_user_id'))
    verif_key = models.TextField(_('verify_key'), unique=True)

    class Meta:
        verbose_name = _('telegram_user_check')
        verbose_name_plural = _('telegram_user_checks')

    def __str__(self):
        return _('%(telegram_user_id)d has verif key %(verif_key)s') % {'telegram_user_id': self.telegram_user_id, 'verif_key': self.verif_key}

# Memorize which telegram user is in which chat
class TelegramUserChat(models.Model):
    telegram_user_id = models.BigIntegerField(_('telegram_user_id'))
    telegram_chat_id = models.BigIntegerField(_('telegram_chat_id'))

    class Meta:
        verbose_name = _('telegram_user_chat')
        verbose_name_plural = _('telegram_user_chats')
        unique_together = ('telegram_user_id', 'telegram_chat_id')

    def __str__(self):
        return _('%(telegram_user_id)d is in the chat %(telegram_chat)d') % {'telegram_user_id': self.telegram_user_id, 'telegram_chat_id': self.telegram_chat_id}

# Memorize the Telegram chats in which the bot are, and the options of them
class TelegramChat(models.Model):
    chat_id = models.BigIntegerField(_('telegram_chat_id'), unique=True)
    # notify_only_members: True: only when somebody we know is in the chat has the
    # seum, we notify the channel
    # notify_only_members: False: we notify the channel for every new seum
    notify_only_members = models.BooleanField(_('notify_only_members'))

    class Meta:
        verbose_name = _('telegram_chat')
        verbose_name_plural = _('telegram_chats')

    def __str__(self):
        return _('%(chat_id)d is a telegram chat, with option notify_only_members to %(notify_only_members)s') % {'chat_id': self.chat_id, 'notify_only_members': self.notify_only_members}
