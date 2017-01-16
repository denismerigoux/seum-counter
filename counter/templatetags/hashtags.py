from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re
from counter.utils import removeAccentsToLowercase
from counter.models import Keyword
from django.core.urlresolvers import reverse

register = template.Library()


@register.filter(needs_autoescape=True, name='hashtag')
def linkifyHashtags(text, autoescape=True):
    parts = re.split(r'(#[^#\s]+)', text)
    result = ''
    for part in parts:
        if autoescape:
            esc = conditional_escape
        else:
            esc = (lambda x: x)
        if re.match(r'#[^#\s]+', part):
            hashtag = removeAccentsToLowercase(part[1:])
            try:
                keyword = Keyword.objects.get(text=hashtag)
                part = '<a href="%s">%s</a>' % (
                    esc(reverse('hashtag', kwargs={'keyword': keyword.text})),
                    esc(part))
            except Keyword.DoesNotExist:
                None
        result += part
    return mark_safe(result)
