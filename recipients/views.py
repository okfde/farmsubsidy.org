from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Sum
from django.conf import settings

from .models import (CountryYear, RecipientYear, Recipient, Payment,
    SchemeYear, Scheme, COUNTRY_CODES)
from .forms import SearchForm
from .pagination import Paginator

LATEST_YEAR = settings.LATEST_YEAR


def home(request):
    # top_eu = RecipientYear.objects.filter(year=LATEST_YEAR)[:10]

    return render(request, 'home.html', {
        'top_eu': [],
        'countries': COUNTRY_CODES.values(),
        'LATEST_YEAR': LATEST_YEAR,
    })


def countries(request):
    countries = []
    min_year = 99999
    max_year = 0
    for code, country in COUNTRY_CODES.items():
        years_max_min = CountryYear.objects.year_max_min(code)
        country_dict = {
            'min_year': years_max_min[0],
            'max_year': years_max_min[1],
        }
        if years_max_min[0] > 0 and years_max_min[0] < min_year:
            min_year = years_max_min[0]
        if years_max_min[1] > 0 and years_max_min[1] > max_year:
            max_year = years_max_min[1]
        countries.append(country_dict)

    years_available = []
    for year in range(min_year, max_year + 1):
        years_available.append(year)

    return render(request, 'countries.html',
        {
            'countries': countries,
            'years_available': years_available,
            'latest_year': settings.LATEST_YEAR,
        })


def country(request, country, year=None):
    """
    Provides all the variables for the country pages at, for example "/AT/"

    Querysets:

    - `top_recipients` Gets n recipients, sorted by total amount for a given year
    - `years` The years that we have data for a given country

    """
    country = country.upper()
    if year is not None:
        year = int(year)

    years_max_min = CountryYear.objects.year_max_min(country)
    years = CountryYear.objects.filter(country=country)

    if year is None:
        top_recipients = Recipient.objects.top_recipients()
        if country != "EU":
            top_recipients = top_recipients.filter(countrypayment=country)
    else:
        top_recipients = RecipientYear.objects.filter(year=year)
        if country != "EU":
            top_recipients = top_recipients.filter(country=country)

    top_recipients = top_recipients[:5]

    # Cache top_recipients
    # top_recipients = QuerySetCache(
    #                    top_recipients,
    #                    key="country.%s.%s.top_recipients" % (country, year),
    #                    cache_type="filesystem")

    if year is None:
        top_schemes = Scheme.objects.top_schemes(country=country)[:5]
    else:
        top_schemes = SchemeYear.objects.top_schemes(year=year, country=country)[:5]

    # Cache top_schemes
    # top_schemes = QuerySetCache(
    #                    top_schemes,
    #                    key="country.%s.%s.top_schemes" % (country, year),
    #                    cache_type="filesystem")

    # top_locations = Location.get_root_nodes().filter(year=year)
    # if country and country != "EU":
    #     top_locations = top_locations.filter(country=country)
    # top_locations = top_locations.order_by('-total')[:5]

    # Cache top_locations
    # top_locations = QuerySetCache(
    #                    top_locations,
    #                    key="country.%s.%s.top_locations" % (country, year),
    #                    cache_type="filesystem")

    # get transparency score
    # transparency = None
    # if country != "EU":
    #     transparency = transparency_score(country)
    # country_info, ci_created = CountryInfo.objects.get_or_create(country=country)

    # get the most recent news story
    # latest_news_item = False
    # news_items = TaggedItem.objects.get_by_model(FeedItems,
    #     Tag.objects.filter(name=country))
    # news_items = news_items.order_by("-date")
    # if news_items:
    #     latest_news_item = news_items[0]

    # get country stats
    # stats_info = None  # load_info(country)

    return render(request,
        'country.html',
        {
            'top_recipients': top_recipients,
            'top_schemes': top_schemes,
            # 'top_locations': top_locations,
            # 'country_info': country_info,
            # 'transparency': transparency,
            # 'latest_news_item': latest_news_item,
            # 'stats_year': settings.STATS_YEAR,
            # 'stats_info': stats_info,
            'years': years,
            'selected_year': year,
            'years_max_min': years_max_min,
            'country': COUNTRY_CODES[country]
        }
    )


def recipient_short(request, country, recipient_id):
    country = country.upper()
    recipient = get_object_or_404(Recipient, pk=recipient_id)
    return redirect(recipient)


def recipient(request, country, recipient_id, name):
    """
    View for recipient page.

    - `country` ISO country, as defined in countryCodes
    - `recipient_id` is actually a globalrecipientid in the date

    """

    country = country.upper()

    recipient = get_object_or_404(Recipient, pk=recipient_id)

    payments = Payment.objects.select_related().filter(recipient=recipient).order_by('-year', '-amounteuro')
    expanded = request.GET.get('expand', False)
    if not expanded:
        # Hack to stop *all* payments getting displayed, when there are sometimes
        # many 'trasactions' per year in the same scheme.
        all_payments = payments.values('year', 'scheme')
        all_payments = all_payments.annotate(amounteuro=Sum('amounteuro'))
        all_payments = all_payments.order_by('-year', '-amounteuro')
        payments = []
        for payment in all_payments:
            p = Payment()
            p.year = payment['year']
            p.amounteuro = payment['amounteuro']
            s = Scheme.objects.get(pk=payment['scheme'])
            p.scheme = s
            payments.append(p)

    recipient_total = recipient.total
    payment_years = list(set(payment.year for payment in payments))

    # lists this recipient is in:
    recipient_lists = []
    # for list_obj in ListItem.objects.filter(object_id=recipient_id):
    #     recipient_lists.append(list_obj.list_id)

    years_max_min = CountryYear.objects.year_max_min(country)
    return render(request, 'recipient.html',
        {
            'recipient': recipient,
            'payments': payments,
            'recipient_total': recipient_total,
            'recipient_lists': recipient_lists,
            'payment_years': payment_years,
            'first_year': 0,
            'years_max_min': years_max_min,
            'expanded': expanded,
        }
    )


def all_schemes(request, country='EU'):
    """
    Scheme browser (replaces generic 'browse' function for schemes)
    """

    schemes = Scheme.objects.filter(total__isnull=False).order_by('-total')

    if country != 'EU':
        schemes = schemes.filter(countrypayment=country)

    # schemes = QuerySetCache(
    #                    schemes,
    #                    key="all_schemes.%s.schemes" % (country,),
    #                    cache_type="filesystem")

    return render(request,
        'all_schemes.html',
        {
            'schemes': schemes,
        }
    )


def scheme(request, country, globalschemeid, name, year=None):
    """
    Show a single scheme and a list of top recipients to get payments under it

    - `country` ISO country, as defined by countryCodes
    - ``globalschemeid` globalschemeid from the data_schemes table in the database
    """
    if year is not None:
        year = int(year)

    scheme = get_object_or_404(Scheme, globalschemeid=globalschemeid)

    # To add one day
    scheme_years = SchemeYear.objects.filter(globalschemeid=scheme)

    # FIXME: find indexes to make this work
    top_recipients = []
    # top_recipients = RecipientSchemeYear.objects.filter(scheme=scheme, year=selected_year).select_related('recipient')

    # top_recipients = CachedCountQuerySetWrapper(top_recipients, key="data.scheme.%s.%s.%s.top_recipients" % (country, globalschemeid, year))

    return render(request,
        'scheme.html',
        {
            'scheme': scheme,
            'scheme_years': scheme_years,
            'selected_year': year,
            'top_recipients': top_recipients,
        }
    )


def browse(request, country):
    """
    Browse recipients, sorted / filtered by various things using django-filter
    """

    country = country.upper()
    recipients = Recipient.objects.order_by('-total').filter(total__isnull=False)

    if country != "EU":
        recipients = recipients.filter(countrypayment=country)
    recipients = recipients.only('name', 'total', 'countrypayment')
    # recipients = CachedCountQuerySetWrapper(queryset=recipients)
    paginator = Paginator(recipients, 30)

    recipients = paginator.page(request.GET.get('page', 1), start=request.GET.get('start', ''))

    return render(request, 'browse.html',
        {
            'recipients': recipients,
            'country': COUNTRY_CODES[country]
        }
    )


def search(request, search_map=False):
    form = SearchForm()
    q = request.GET.get('q', '')
    total = 0
    offset = 0
    sqs = None
    list_search = None
    location_search = None
    feature_search = None

    if q:
        form = SearchForm(initial={'q': q})

        auto_q = AutoQuery(q)
        sqs = SearchQuerySet().models(Recipient).facet('country').filter(content=auto_q)
        if request.GET.get('country', None) is not None:
            sqs = sqs.filter(country=request.GET['country'])

        total = 0
        offset = 0
        if request.GET.get('page'):
            offset = 20 * (int(request.GET.get('page')) - 1)
        for t in sqs[offset:offset + 20]:
            if t.total:
                total += t.total
        len(sqs)

    if search_map:
        t = 'map.html'
    else:
        t = 'results.html'
    return render(request, t,
        {
            'q': q,
            'total': total,
            'offset': offset,
            'form': form,
            'sqs': sqs,
            'list_search': list_search,
            'location_search': location_search,
            'feature_search': feature_search
        }
    )
