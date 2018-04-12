from django.urls import re_path

from .models import COUNTRY_CODES
from .views import (home, countries, country, recipient_short, recipient,
    all_schemes, scheme, browse, search)


def country_url(pattern, *args, **kwargs):
    """
    Wrap url() with a URL that always prepends a list of countries (upper and
    lower case)
    """
    countries = [c for c in COUNTRY_CODES.keys()]
    countries = "|".join(countries)
    return re_path(r'^(?i)(?P<country>%s)/%s' % (countries, pattern), *args, **kwargs)


urlpatterns = [
    re_path(r'^$', home, name='home'),
    re_path(r'countries/', countries, name='countries'),
    re_path(r'search/', search, name='search'),
    country_url(r'$', country, name='country'),
    country_url(r'(?P<year>\d+)/$', country, name='country_year'),
    country_url(r'recipient/(?P<recipient_id>[^/]+)/$', recipient_short, name='recipient_short_view'),
    country_url(r'recipient/(?P<recipient_id>[^/]+)/(?P<name>(.*))/', recipient, name='recipient_view'),

    # Locations
    # country_url(r'location/(?P<year>\d+)/(?P<slug>([^\d]+))/$', location, name='location_view'),
    # country_url(r'location/(?P<slug>([^\d]+))/$', location, name='location_view' ),

    # country_url(r'location/(?P<year>\d+)/$', all_locations, name='all_locations'),
    # country_url(r'location/$', all_locations, name='all_locations' ),

    # Schemes
    country_url(r'scheme/$', all_schemes, name='all_schemes'),
    country_url(r'scheme/(?P<globalschemeid>[^/]+)/(?P<name>(.*))/(?P<year>(\d+))/', scheme, name='scheme_view'),
    country_url(r'scheme/(?P<globalschemeid>[^/]+)/(?P<name>(.*))/', scheme, name='scheme_view'),


    country_url(r'browse/', browse, name='browse'),
    country_url(r'browse/(?P<browse_type>(recipient|scheme|location))/(?P<year>\d+)/(?P<sort>(amount|name))', browse, name='browse'),
    country_url(r'browse/(?P<browse_type>(recipient|scheme|location))', browse,
        name='browse_default'),
]
