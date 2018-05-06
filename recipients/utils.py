from django.urls import reverse

from slugify import slugify
import elasticsearch_dsl


def slugify_recipient(value):
    s = (flat_es(value.name), flat_es(value.postcode or value.location))
    return slugify('-'.join(s))


def get_recipient_url(recipient):
    return reverse('recipient_view', kwargs={
        'country': recipient.country,
        'recipient_id': recipient.meta.id,
        'slug': slugify_recipient(recipient)
    })


def prepare_recipient_list(recipients):
    for r in recipients:
        prepare_recipient(r)


def prepare_recipient(recipient):
    recipient.name_list = recipient.name
    recipient.name = flat_es(recipient.name)

    recipient.postcode_list = recipient.postcode
    recipient.postcode = flat_es(recipient.postcode)


def flat_es(value):
    if isinstance(value, elasticsearch_dsl.utils.AttrList):
        if value:
            return value[0]
        return ''
    return value
