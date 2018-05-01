from django.shortcuts import redirect, render, Http404
from django.http import QueryDict
from django.core.paginator import EmptyPage

from elasticsearch_dsl import (
    A, FacetedSearch, TermsFacet, RangeFacet
)

from .models import COUNTRY_CODES
from .forms import SearchForm
from .es_models import Recipient
from .utils import (
    get_recipient_url, prepare_recipient_list, prepare_recipient,
    ElasticPaginator
)


class RecipientSearch(FacetedSearch):
    doc_types = [Recipient, ]
    # fields that should be searched
    fields = ['name', 'location', 'address', 'postcode']

    facets = {
        'country': TermsFacet(field='country'),
        # 'year': NestedFacet('payments', DateHistogramFacet(field='year')),
        'total_amount': RangeFacet(field='total_amount', ranges=[
            ("few", (None, 2)),
            ("lots", (2, None))
        ])
    }


def home(request):
    top_eu = Recipient.search().sort('-total_amount')[:5].execute()
    return render(request, 'home.html', {
        'countries': COUNTRY_CODES.values(),
        'top_eu': top_eu
    })


def countries(request):
    s = Recipient.search()
    a = A('nested', path='payments')
    by_country = a.bucket('per_country', 'terms', field='payments.country')
    by_country.metric(
        'years', 'date_histogram',
        field='payments.year',
        interval='year'
    )
    by_country.metric(
        'total_amount', 'sum',
        field='payments.amount'
    )
    s.aggs.bucket('nested_payments', a)
    s = s.source(False)
    response = s.execute()
    countries = []
    country_buckets = response.aggregations.nested_payments.per_country.buckets
    for country_agg in country_buckets:
        countries.append({
            'code': country_agg['key'],
            'name': COUNTRY_CODES[country_agg['key']],
            'total_amount': country_agg['total_amount']['value'],
            'min_year': country_agg['years']['buckets'][0]['key_as_string'][:4],
            'max_year': country_agg['years']['buckets'][-1]['key_as_string'][:4],
        })

    return render(request, 'recipients/countries.html',
        {
            'countries': countries,
        })


def country(request, country, year=None):
    """
    Provides all the variables for the country pages at, for example "/AT/"

    Querysets:

    - `top_recipients` Gets n recipients, sorted by total amount for a given year
    - `years` The years that we have data for a given country

    """
    country = country.upper()
    filters = {
        'country': country
    }
    # if year is not None:
    #     filters['year']
    #

    s = (
        Recipient.search()
        .filter('term', **filters)
        .sort('-total_amount')[:5]
    )
    print(s.to_dict())

    top_recipients = s.execute()

    prepare_recipient_list(top_recipients)

    return render(request,
        'recipients/country.html',
        {
            'top_recipients': top_recipients,
            'country': COUNTRY_CODES[country]
        }
    )


def recipient_short(request, country, recipient_id):
    country = country.upper()
    if not recipient_id.startswith(country):
        raise Http404
    recipient = Recipient.get(id=recipient_id)
    return redirect(get_recipient_url(recipient))


def recipient(request, country, recipient_id, slug):
    """
    View for recipient page.

    - `country` ISO country, as defined in countryCodes
    - `recipient_id` is actually a globalrecipientid in the date

    """

    country = country.upper()
    if not recipient_id.startswith(country):
        raise Http404

    recipient = Recipient.get(id=recipient_id)

    prepare_recipient(recipient)

    return render(request, 'recipients/recipient.html',
        {
            'recipient': recipient,
            'payments': recipient.payments,
            'recipient_total': recipient.total_amount,
            'country': COUNTRY_CODES[recipient.country]
        }
    )


def search(request, search_map=False):
    PAGE_SIZE = 20

    form = SearchForm()
    q = request.GET.get('q', '')
    offset = 0

    filters = {}

    if q and len(q) > 2:
        form = SearchForm(initial={'q': q})

    if request.GET.get('country', None) is not None:
        filters['country'] = request.GET['country']

    rs = RecipientSearch(q, filters)

    offset = 0
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    offset = PAGE_SIZE * (page - 1)
    rs = rs[offset:offset + PAGE_SIZE]
    response = rs.execute()

    prepare_recipient_list(response)

    paginator = ElasticPaginator(response, PAGE_SIZE)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    cleaned_query = QueryDict(request.GET.urlencode().encode('utf-8'),
                              mutable=True)

    cleaned_query.pop('page', None)
    getvars = '&' + cleaned_query.urlencode()

    return render(
        request, 'recipients/search.html',
        {
            'query': q,
            'total': response.hits.total,
            'offset': offset,
            'form': form,
            'object_list': page_obj,
            'facets': response.facets,
            'paginator': paginator,
            'getvars': getvars
        }
    )
