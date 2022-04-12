from collections import OrderedDict

from django.utils.translation import gettext_lazy as _


class Country:
    def __init__(self, code, name):
        self.code = code
        self.code_lower = code.lower()
        self.name = name

    def __str__(self):
        return str(self.name)


COUNTRY_CODES = OrderedDict([
    ('EU', _('All Countries')),
    ('AT', _('Austria')),
    ('BE', _('Belgium')),
    ('BG', _('Bulgaria')),
    ('CY', _('Cyprus')),
    ('CZ', _('Czech Republic')),
    ('DK', _('Denmark')),
    ('EE', _('Estonia')),
    ('FI', _('Finland')),
    ('FR', _('France')),
    ('DE', _('Germany')),
    ('GR', _('Greece')),
    ('HU', _('Hungary')),
    ('IE', _('Ireland')),
    ('IT', _('Italy')),
    ('LV', _('Latvia')),
    ('LT', _('Lithuania')),
    ('LU', _('Luxembourg')),
    ('MT', _('Malta')),
    ('NL', _('Netherlands')),
    ('PL', _('Poland')),
    ('PT', _('Portugal')),
    ('RO', _('Romania')),
    ('SK', _('Slovakia')),
    ('SI', _('Slovenia')),
    ('ES', _('Spain')),
    ('SE', _('Sweden')),
    ('GB', _('United Kingdom')),
])
for code in COUNTRY_CODES:
    COUNTRY_CODES[code] = Country(code, COUNTRY_CODES[code])
