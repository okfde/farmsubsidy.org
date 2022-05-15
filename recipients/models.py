from collections import OrderedDict
from slugify import slugify

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from farmsubsidy_store import model, search


class Payment(model.Payment):
    pass


class Recipient(model.Recipient):
    def get_slug(self):
        return slugify(self.name[0])

    def get_absolute_url(self):
        return reverse(
            "recipient_view",
            kwargs={
                "country": self.country[0],
                "recipient_id": self.id,
                "slug": self.get_slug(),
            },
        )

    @classmethod
    def search(cls, q: str) -> search.Query:
        return search.RecipientNameSearch(q).query()


class Scheme(model.Scheme):
    def get_absolute_url(self):
        pass


class Year(model.Year):
    def get_absolute_url(self):
        return reverse("search") + f"?year={self.year}"


class Country(model.Country):
    @property
    def min_year(self):
        return min(self.years)

    @property
    def max_year(self):
        return max(self.years)

    @property
    def code(self):
        return self.country

    @property
    def code_lower(self):
        return self.country.lower()

    @property
    def name(self):
        return COUNTRY_CODES[self.code]

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("country", kwargs={"country": self.code})


COUNTRY_CODES = OrderedDict(
    [
        ("search", _("All Countries")),
        ("AT", _("Austria")),
        ("BE", _("Belgium")),
        ("BG", _("Bulgaria")),
        ("CY", _("Cyprus")),
        ("CZ", _("Czech Republic")),
        ("DK", _("Denmark")),
        ("EE", _("Estonia")),
        ("FI", _("Finland")),
        ("FR", _("France")),
        ("DE", _("Germany")),
        ("GR", _("Greece")),
        ("HU", _("Hungary")),
        ("HR", _("Croatia")),
        ("IE", _("Ireland")),
        ("IT", _("Italy")),
        ("LV", _("Latvia")),
        ("LT", _("Lithuania")),
        ("LU", _("Luxembourg")),
        ("MT", _("Malta")),
        ("NL", _("Netherlands")),
        ("PL", _("Poland")),
        ("PT", _("Portugal")),
        ("RO", _("Romania")),
        ("SK", _("Slovakia")),
        ("SI", _("Slovenia")),
        ("ES", _("Spain")),
        ("SE", _("Sweden")),
        ("GB", _("United Kingdom")),
    ]
)
