from django.contrib import admin

# Register your models here.
from .models import Counter,Reset

admin.site.register(Counter)
admin.site.register(Reset)
