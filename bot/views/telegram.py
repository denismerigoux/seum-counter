from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.utils import IntegrityError
from django.conf import settings
from counter.views.counter import perform_reset

import json
import requests
import random
import string
import re

from counter.models import Counter, Reset
from bot.models import TelegramUser, TelegramUserCheck, TelegramUserChat, TelegramChat

telegram_ips = ['149.154.' + str(i) + '.' for i in range(160, 176)] + ['91.108.' + str(i) + '.' for i in range(4, 8)]
telegram_url = 'https://api.telegram.org/bot' + settings.BOT_TELEGRAM_KEY + '/'
telegram_bot_id = settings.BOT_TELEGRAM_ID
telegram_bot_name = settings.BOT_TELEGRAM_NAME

@receiver(post_save, sender=Reset)
def notify_telegram(sender, instance, created, **kwargs):
    if not settings.BOT_TELEGRAM_KEY or not settings.BOT_TELEGRAM_ID or not settings.BOT_TELEGRAM_NAME:
        return
    if created:
        chat_ids = [e.chat_id for e in TelegramChat.objects.filter(notify_only_members=False)]
        try:
            telegram_user = TelegramUser.objects.get(counter=instance.counter)
            chats = TelegramUserChat.objects.filter(telegram_user_id=telegram_user.telegram_user_id)
            chat_ids = chat_ids + [e.telegram_chat_id for e in chats]
        except TelegramUser.DoesNotExist:
            do_nothing = True

        if instance.who is None or instance.who == instance.counter:
            message = str(instance.counter) + ' a le seum: ' + instance.reason
        else:
            message = str(instance.who) + ' a foutu le seum à ' + str(instance.counter) + ': ' + instance.reason

        for chat_id in set(chat_ids):
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat_id, 'text': message})

@login_required
def link(request, verif_key):
    try:
        telegram_user_check = TelegramUserCheck.objects.get(verif_key=verif_key)
        the_counter = Counter.objects.get(user__id=request.user.id)
        TelegramUser.objects.create(counter=the_counter, telegram_user_id=telegram_user_check.telegram_user_id)
        TelegramUserCheck.objects.filter(telegram_user_id=telegram_user_check.telegram_user_id).delete()
        return HttpResponse('Your Telegram account has been linked!')
    except TelegramUserCheck.DoesNotExist:
        return HttpResponse(status=404)

@csrf_exempt
def webhook(request):
    ip = re.sub(r"\.([^.]+)$", '.', request.META.get('REMOTE_ADDR'))

    if not ip in telegram_ips:
        return HttpResponse(status=401)

    data = json.loads(request.body.decode('utf-8'))
    print(data)

    # We have different types of messages
    # - a simple text message from a person
    # - the bot joined/left a channel
    # - somebody joined/left a channel
    # The idea is to keep a list of all the telegram users in all channels
    # Then when a new seum is created, we look all the channels in which this user
    # is, and we send a message in those to notify everybody

    if not 'message' in data or not 'chat' in data['message']:
        return HttpResponse(201) # we should return something correct, or Telegram will try to send us the message again multiple times

    chat = data['message']['chat']

    if chat['type'] != 'private':
        if 'new_chat_member' in data['message']:
            user_id = data['message']['new_chat_member']['id']
            if user_id == telegram_bot_id:
                r = requests.get(telegram_url + 'getChatMembersCount?chat_id=' + str(chat['id'])).json()
                if r['result'] < 20: # when there are less than 20 people, we deactivate notify_only_members
                    try:
                        TelegramChat.objects.create(chat_id=chat['id'], notify_only_members=True)
                    except IntegrityError as e:
                        print(e)
                        return HttpResponse('')
                    requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Hello everyone! Because of Telegram restrictions, I don\'t know who is here :( . Everybody, please say /seumhello, so I can see you\'re here!'})
                else:
                    TelegramChat.objects.create(chat_id=chat['id'], notify_only_members=False)
                    requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Hello everyone! I will notify you everytime a person in the world has the seum. I you prefer to be notified only when a member of this group has the seum, use the command /notify_every_seum_or_not'})
            else:
                TelegramUserChat.objects.create(telegram_user_id=user_id, telegram_chat_id=chat['id'])
            return HttpResponse('')

        if 'left_chat_member' in data['message']:
            user_id = data['message']['left_chat_member']['id']
            if user_id == telegram_bot_id:
                TelegramUserChat.objects.filter(telegram_chat_id=chat['id']).delete()
                TelegramChat.objects.filter(chat_id=chat['id']).delete()
            else:
                TelegramUserChat.objects.filter(telegram_user_id=user_id, telegram_chat_id=chat['id']).delete()
            return HttpResponse(200)

    if not 'message' in data or not 'from' in data['message'] or not 'id' in data['message']['from']:
        return HttpResponse(201)

    telegram_user_id = data['message']['from']['id']

    if chat['type'] != 'private':
        # For each message we receive in a non private chat, we save that this user is in this chat
        try:
            TelegramUserChat.objects.create(telegram_user_id=telegram_user_id, telegram_chat_id=chat['id'])
        except:
            do_nothing = True

    if not 'text' in data['message']:
        return HttpResponse(201)

    text = data['message']['text'].strip()
    if text == '/notify_every_seum_or_not' or text == '/notify_every_seum_or_not@' + telegram_bot_name:
        tchat = TelegramChat.objects.get(chat_id=chat['id'])
        tchat.notify_only_members = not tchat.notify_only_members
        if tchat.notify_only_members:
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Ok, I will notify you only if someone in the group has the seum. But, because of Telegram restrictions, I don\'t know who is here :( . Everybody, please say /seumhello, so I can see you\'re here!'})
        else:
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Ok, so now I will notify you everytime a person in the world has the seum.'})
        tchat.save()

    try:
        telegram_user = TelegramUser.objects.get(telegram_user_id=telegram_user_id)
        # in that cas we need to parse the message
        # and either create a new seum and reset a counter
        # either like some existing seum

        if text == '/seumunlink' or text == '/seumunlink@' + telegram_bot_name:
            TelegramUser.objects.filter(telegram_user_id=telegram_user_id).delete()
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Your Telegram account has successfully been unlinked from your SeumBook account', 'reply_to_message_id': data['message']['message_id']})
            return HttpResponse('')

        if text == '/seumhello' or text == '/seumhello@' + telegram_bot_name:
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Hello ' + telegram_user.counter.name + ' :-)', 'reply_to_message_id': data['message']['message_id']})
            return HttpResponse('')

        seum_cmd = r"^/seum((@" + telegram_bot_name + ")?)\s+(.+)$"
        if re.match(seum_cmd, text) is not None:
            # it's a /seum cmd
            m = re.sub(seum_cmd, r"\3", text)
            maybe_counter = m.split(' ')[0]
            try:
                yes_counter = Counter.objects.get(trigramme=maybe_counter)
                seum_message = ' '.join(m.split(' ')[1:])
            except Counter.DoesNotExist:
                yes_counter = telegram_user.counter
                seum_message = m

            perform_reset(telegram_user.counter, yes_counter, seum_message)
    except TelegramUser.DoesNotExist:
        print('in that case we send a link to the user')
        if chat['type'] == 'private' and chat['id'] == telegram_user_id:
            # We are in a private channel, we directly send the link
            verif_key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(30))
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Open the following URL to link your Telegram account to your SeumBook account: ' + request.build_absolute_uri(reverse('tellink', args=[verif_key]))})
            TelegramUserCheck.objects.create(telegram_user_id=telegram_user_id, verif_key=verif_key)
        else:
            print('bou')
            # We are not in a private channel, so we mention the user to talk with us
            requests.post(telegram_url + 'sendMessage', json={'chat_id': chat['id'], 'text': 'Your Telegram account isn\'t linked to a SeumBook account. Say hello to me in a private chat to link it :-)! https://telegram.me/' + telegram_bot_name + '?start=Hello', 'reply_to_message_id': data['message']['message_id']})

    return HttpResponse('')
