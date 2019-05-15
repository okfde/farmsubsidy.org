from django.shortcuts import redirect, render, Http404
from django.http import QueryDict
from django.views.decorators.cache import cache_page

from elasticsearch_dsl import A
from elasticsearch.exceptions import ElasticsearchException

from .models import COUNTRY_CODES
from .forms import SearchForm
from .es_models import Recipient
from .utils import (
    get_recipient_url, prepare_recipient_list, prepare_recipient,
    slugify_recipient
)


@cache_page(None)
def home(request):
    top_eu = Recipient.search().sort('-total_amount')[:5].execute()
    return render(request, 'home.html', {
        'countries': COUNTRY_CODES.values(),
        'top_eu': top_eu
    })


@cache_page(None)
def countries(request):
    s = Recipient.search()
    a = A('nested', path='payments')
    by_country = a.bucket(
        'per_country', 'terms',
        field='payments.country',
        size=len(COUNTRY_CODES)
    )
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

    return render(
        request,
        'recipients/countries.html',
        {
            'countries': countries,
        }
    )


@cache_page(None)
def country(request, country, year=None):
    """
    Provides all the variables for the country pages at, for example "/AT/"

    Querysets:

    - `top_recipients` Gets n recipients, sorted by total amount for a given year
    - `years` The years that we have data for a given country

    """
    country = country.upper()

    s = Recipient.search()
    s = s.filter('term', country=country)
    if year is not None:
        s = s.filter('nested', path='payments', query={
            'bool': {'must': [{'term': {'payments.year': int(year)}}]}
        })

    a = A('nested', path='payments')
    by_year = a.bucket(
        'per_year', 'date_histogram',
        field='payments.year',
        interval='year'
    )
    by_year.metric(
        'total_amount', 'sum',
        field='payments.amount'
    )
    s.aggs.bucket('nested_payments', a)

    s = s.sort('-total_amount')[:5]

    top_recipients = s.execute()

    year_amounts = [{
        'year': int(x['key_as_string'][:4]),
        'amount': x['total_amount']['value'],
        'recipients': x['doc_count']
    } for x in top_recipients.aggregations.nested_payments.per_year.buckets]

    prepare_recipient_list(top_recipients)

    return render(
        request,
        'recipients/country.html',
        {
            'year': year,
            'top_recipients': top_recipients,
            'year_amounts': year_amounts,
            'country': COUNTRY_CODES[country]
        }
    )


def recipient_short(request, country, recipient_id):
    country = country.upper()
    if not recipient_id.startswith(country):
        raise Http404

    try:
        recipient = Recipient.get(id=recipient_id)
    except ElasticsearchException:
        return render(request, '503.html', {}, status=503)

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

    try:
        recipient = Recipient.get(id=recipient_id)
    except ElasticsearchException:
        return render(request, '503.html', {}, status=503)

    prepare_recipient(recipient)

    if slugify_recipient(recipient) != slug:
        return redirect(get_recipient_url(recipient))

    similar = Recipient.search()
    similar = similar.query('more_like_this', like=[
        {'_id': recipient.meta.id}
        ], fields=['name'], min_term_freq=1)
    similar = similar.execute()

    prepare_recipient_list(similar)

    return render(
        request,
        'recipients/recipient.html',
        {
            'recipient': recipient,
            'payments': recipient.payments,
            'recipient_total': recipient.total_amount,
            'country': COUNTRY_CODES[recipient.country],
            'similar': similar
        }
    )


def make_pagination(recipient):
    return ','.join([str(recipient['total_amount']), recipient.meta.id])


def parse_pagination(token):
    parts = token.split(',', 1)
    if len(parts) != 2:
        return None
    try:
        parts[0] = float(parts[0])
    except ValueError:
        return None
    return parts


def search(request, search_map=False):
    PAGE_SIZE = 20

    form = SearchForm()
    q = request.GET.get('q', '')
    filters = {}

    if request.GET.get('country', None) is not None:
        if request.GET['country'] in COUNTRY_CODES:
            filters['country'] = request.GET['country']

    if request.GET.get('year', None) is not None:
        try:
            filters['year'] = int(request.GET['year'])
        except ValueError:
            pass

    s = Recipient.search()

    if q and len(q) > 2:
        form = SearchForm(initial={'q': q})

        s = s.query("multi_match", query=q, type='cross_fields', fields=[
                'name', 'location', 'address', 'postcode'
            ], operator="and",
        )

    if 'country' in filters:
        s = s.filter('term', country=filters['country'])

    if 'year' in filters:
        s = s.filter('nested', path='payments', query={
            'bool': {'must': [{'term': {
                'payments.year': filters['year']
            }}]}
        })
    agg_country = A('terms', field='country', size=len(COUNTRY_CODES))
    agg_year = A('nested', path='payments')
    agg_year_bucket = agg_year.bucket(
        'year', 'date_histogram',
        field='payments.year',
        interval='year'
    )
    agg_year_bucket.metric('amount', 'sum', field='payments.amount')
    s.aggs.bucket('country', agg_country)
    s.aggs.bucket('year', agg_year)
    s.aggs.metric('total_amount', 'sum', field='total_amount')

    if request.GET.get('next'):
        next_token = parse_pagination(request.GET['next'])
        if next_token is not None:
            s = s.extra(search_after=next_token)
    s = s.sort('-total_amount', '_id')

    s = s[:PAGE_SIZE]
    response = s.execute()

    prepare_recipient_list(response)

    cleaned_query = QueryDict(request.GET.urlencode().encode('utf-8'),
                              mutable=True)

    cleaned_query.pop('next', None)
    cleaned_query.pop('prev', None)
    getvars = '&' + cleaned_query.urlencode()

    try:
        next_token = make_pagination(response[-1])
    except IndexError:
        next_token = None

    aggregations = {
        'year': [{
            'key': 'year',
            'name': x['key_as_string'][:4],
            'value': int(x['key_as_string'][:4]),
            'amount': x['amount']['value'],
            'count': x['doc_count'],
            'count_label': 'records',
            'selected': int(x['key_as_string'][:4]) == filters.get('year')
        } for x in response.aggregations.year.year.buckets],
        'country': [{
            'key': 'country',
            'name': COUNTRY_CODES[x['key']],
            'value': x['key'],
            'count': x['doc_count'],
            'count_label': 'recipients',
            'selected': x['key'] == filters.get('country')
        } for x in response.aggregations.country.buckets],
        'total_amount': response.aggregations.total_amount
    }

    return render(
        request, 'recipients/search.html',
        {
            'query': q,
            'total': response.hits.total,
            'form': form,
            'next_token': next_token,
            'object_list': response,
            'filters': filters,
            'aggregations': aggregations,
            'getvars': getvars,
            'querydict': cleaned_query,
        }
    )
