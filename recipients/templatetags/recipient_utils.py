from __future__ import unicode_literals

from django import template
from django.template.defaultfilters import floatformat
from django.contrib.humanize.templatetags.humanize import intcomma

from ..utils import get_recipient_url, flat_es
from ..models import COUNTRY_CODES

register = template.Library()


@register.filter
def recipient_url(recipient):
    return get_recipient_url(recipient)


@register.filter
def format_list(value):
    return flat_es(value)


@register.filter
def get_country_name(value):
    return COUNTRY_CODES.get(value)


@register.filter
def intcomma_floatformat(value, arg=2):
    if value is None:
        return None

    DECIMAL_SEPARATOR = floatformat(0.0, 2)[1]

    value = round(value, arg)

    val = intcomma(value)
    if DECIMAL_SEPARATOR not in val:
        if arg > 0:
            val += '%s%s' % (DECIMAL_SEPARATOR, '0' * arg)
    else:
        before_ds, after_ds = val.rsplit(DECIMAL_SEPARATOR, 1)
        if len(after_ds) > arg:
            after_ds = after_ds[:arg]
        elif len(after_ds) < arg:
            after_ds += '0' * (arg - len(after_ds))
        if arg > 0:
            val = '%s%s%s' % (before_ds, DECIMAL_SEPARATOR, after_ds)
        else:
            val = before_ds
    return val


@register.filter(name='listify')
def listify(value):
    return list(value)


@register.simple_tag
def get_facet_link(querydict, key, value=None):
    qd = querydict.copy()
    qd.pop(key, None)
    if value is not None:
        qd[key] = value
    return '?' + qd.urlencode()
