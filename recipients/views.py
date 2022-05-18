from django.http import QueryDict
from django.shortcuts import Http404, redirect, render
from django.urls import reverse
from django.utils.html import escape
from django.views.decorators.cache import cache_page
from farmsubsidy_store.aggregations import agg_by_country, agg_by_year, amount_sum
from farmsubsidy_store.drivers import get_driver
from farmsubsidy_store.search import RecipientSearchView
from farmsubsidy_store.model import Payment
from farmsubsidy_store.query import Query

from .forms import SearchForm
from .models import COUNTRY_CODES, Country, Recipient


@cache_page(None)
def home(request):
    top_ids_query = (
        Query(driver=get_driver())
        .select("recipient_id", "sum(amount) as amount_sum")
        .group_by("recipient_id")
        .order_by("-amount_sum")[:5]
    )
    top_ids = [row["recipient_id"] for row in top_ids_query]
    top_eu = (
        Recipient.select().where(recipient_id__in=top_ids).order_by("-amount_sum")[:5]
    )
    return render(
        request, "home.html", {"countries": COUNTRY_CODES.items(), "top_eu": top_eu}
    )


@cache_page(None)
def countries(request):
    countries = Country.select()
    return render(
        request,
        "recipients/countries.html",
        {
            "countries": countries,
        },
    )


@cache_page(None)
def country(request, country, year=None):
    """
    Provides all the variables for the country pages at, for example "/AT/"

    Querysets:

    - `top_recipients` Gets n recipients, sorted by total amount for a given year
    - `years` The years that we have data for a given country

    """
    country = Country.get(country.upper())
    top_recipients = country.get_recipients().order_by("-amount_sum")[:5]
    if year is not None:
        top_recipients = top_recipients.where(year=year)

    return render(
        request,
        "recipients/country.html",
        {
            "year": year,
            "top_recipients": top_recipients,
            "country": country,
        },
    )


def recipient_short(request, country, recipient_id):
    recipient = Recipient.get(recipient_id)
    if recipient is None:
        raise Http404
    return redirect(recipient.get_absolute_url())


@cache_page(None)
def recipient(request, country, recipient_id, slug):
    """
    View for recipient page.

    - `country` ISO country, as defined in countryCodes
    - `recipient_id` is actually a globalrecipientid in the date

    """

    recipient = Recipient.get(recipient_id)
    if recipient is None:
        # redirect to search view to try to not break old urls:
        return redirect(reverse("search") + slug)

    if recipient.get_slug() != slug:
        return redirect(recipient.get_absolute_url())

    similar = Recipient.search(recipient)[:10]
    similar = [r for r in similar if r.id != recipient.id]

    return render(
        request,
        "recipients/recipient.html",
        {
            "recipient": recipient,
            "payments": recipient.get_payments(),
            "recipient_total": recipient.amount_sum,
            "country": recipient.get_countries().first(),
            "similar": similar,
        },
    )


@cache_page(None)
def search(request, search_map=False):
    ORDER_BY = "-amount_sum"
    PAGE_SIZE = 20
    form = SearchForm()
    search_params = {escape(k): escape(v) for k, v in request.GET.items() if v.strip()}
    if not search_params:  # at least filter down a bit
        search_params = {"year": 2020}
    view_kwargs = {
        **{"order_by": ORDER_BY},  # may be overwritten from GET param
        **search_params,
        **{"limit": PAGE_SIZE},  # ensure limit always
    }

    view = RecipientSearchView()
    results = view.get_results(**view_kwargs)
    payments = Payment.select().where(recipient_id__in=[x.id for x in results])
    payment_results = payments.execute()  # .merge(results, on="recipient_id", how="left")

    q = view.q
    if q:
        form = SearchForm(initial={"q": q})

    cleaned_query = QueryDict(request.GET.urlencode().encode("utf-8"), mutable=True)

    cleaned_query.pop("p", None)
    getvars = "&" + cleaned_query.urlencode()

    agg_params = view.params.copy()
    if q:
        search_str = view.search_cls(q).get_search_string()
        agg_params.update(recipient_fingerprint__like=f"%{search_str}%")

    aggregations = {
        "year": [
            {
                "key": "year",
                "name": str(row["year"]),
                "value": row["year"],
                "amount": row["amount_sum"],
                "count": row["total_recipients"],
                "count_label": "records",
                "selected": str(row["year"]) == view.params.get("year"),
            }
            for _, row in agg_by_year(**agg_params).iterrows()
        ],
        "country": [
            {
                "key": "country",
                "name": COUNTRY_CODES[row["country"]],
                "value": row["country"],
                "count": row["total_recipients"],
                "count_label": "recipients",
                "selected": row["country"] == view.params.get("country"),
            }
            for _, row in agg_by_country(**agg_params).iterrows()
        ],
        "total_amount": amount_sum(**agg_params),
    }

    return render(
        request,
        "recipients/search.html",
        {
            "query": q or "",
            "total": view.query.count,
            "form": form,
            "next_page": view.page + 1 if view.has_next else None,
            "prev_page": view.page - 1 if view.has_prev else None,
            "object_list": results,
            "object_list_dict": payment_results.to_dict(orient="list"),
            "filters": view.params,
            "aggregations": aggregations,
            "getvars": getvars,
            "querydict": cleaned_query,
        },
    )
