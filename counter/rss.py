from django.contrib.syndication.views import Feed
from counter.models import Counter, Reset
from django.core.urlresolvers import reverse
from babel.dates import format_datetime
from django.utils import timezone
from datetime import timedelta


class SeumFeed(Feed):
    title = "Flil du seum"
    link = "/rss"
    description = "Notifications seumesques"

    def items(self):
        return Reset.objects.filter(timestamp__gte=timezone.now() -
                                    timedelta(days=7)).order_by('-timestamp')

    def item_title(self, item):
        return (item.counter.trigramme + ' (' + item.counter.name +
                ') a eu le seum')

    def item_description(self, item):
        return (format_datetime(item.timestamp, locale='fr',
                                format="dd/MM/Y 'à' HH:mm") +
                ' : ' + item.reason)

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return reverse('counter', args=[item.counter.id])
