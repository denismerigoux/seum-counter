import re
import unicodedata
from counter.models import Keyword


# Analyse the reason of the reset and retrieve all the keyword objects that it
# contains, creating the objects in the DB on-the-fly if necessary
def parseSeumReason(reason):
    hashtags = re.findall(r'(?<=#)[^#\s]+', reason, re.I)
    hashtags = [removeAccentsToLowercase(u) for u in hashtags]
    keywords = []
    for hashtag in hashtags:
        try:
            keyword = Keyword.objects.get(text=hashtag)
            keywords.append(keyword)
        except Keyword.DoesNotExist:
            keyword = Keyword(text=hashtag)
            keyword.save()
            keywords.append(keyword)
    return keywords


def removeAccentsToLowercase(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c.lower() for c in nfkd_form
                     if not unicodedata.combining(c)])
