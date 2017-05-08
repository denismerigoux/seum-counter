from django.contrib import admin

# Register your models here.
from .models import TelegramUser, TelegramUserCheck, TelegramUserChat, TelegramChat

admin.site.register(TelegramUser)
admin.site.register(TelegramUserCheck)
admin.site.register(TelegramUserChat)
admin.site.register(TelegramChat)
