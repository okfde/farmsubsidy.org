from django.urls import re_path, path, include

from .models import COUNTRY_CODES
from .views import (
    home,
    countries, country,
    recipient_short, recipient,
    search
)


def country_url(pattern, *args, **kwargs):
    """
    Wrap url() with a URL that always prepends a list of countries (upper and
    lower case)
    """
    countries = [c for c in COUNTRY_CODES.keys()]
    countries = countries + [c.lower() for c in countries]
    countries = "|".join(countries)
    return re_path(r'^(?P<country>%s)/%s' % (countries, pattern), *args, **kwargs)


urlpatterns = [
    re_path(r'^$', home, name='home'),
    re_path(r'countries/', countries, name='countries'),
    re_path(r'search/', search, name='search'),
    country_url(r'$', country, name='country'),
    country_url(r'(?P<year>\d+)/$', country, name='country_year'),
    country_url(r'recipient/(?P<recipient_id>[^/]+)/$', recipient_short, name='recipient_short_view'),
    country_url(r'recipient/(?P<recipient_id>[^/]+)/(?P<slug>(.*))/', recipient, name='recipient_view'),
    path('', include('django.contrib.flatpages.urls')),

]
