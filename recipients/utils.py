from django.urls import reverse
from django.core.paginator import Paginator, Page


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


class ElasticPaginator(Paginator):
    """
    Override Django's built-in Paginator class to take in a count/total number of items;
    Elasticsearch provides the total as a part of the query results, so we can minimize hits.
    """
    @property
    def count(self):
        return self.object_list.hits.total

    def page(self, number):
        # this is overridden to prevent any slicing of the object_list - Elasticsearch has
        # returned the sliced data already.
        number = self.validate_number(number)
        return Page(self.object_list, number, self)
