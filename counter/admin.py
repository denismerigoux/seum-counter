from django.contrib import admin

# Register your models here.
from .models import Counter, Reset, Like, Keyword, Hashtag

admin.site.register(Counter)
admin.site.register(Reset)
admin.site.register(Like)
admin.site.register(Keyword)
admin.site.register(Hashtag)
