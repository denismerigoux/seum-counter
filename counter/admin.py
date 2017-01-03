from django.contrib import admin

# Register your models here.
from .models import Counter, Reset, Like

admin.site.register(Counter)
admin.site.register(Reset)
admin.site.register(Like)
