from collections import OrderedDict

from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
# from treebeard.mp_tree import MP_Node

from .managers.recipients import RecipientManager
from .managers.recipient_year import RecipientYearManager
from .managers.schemes import SchemeManager, SchemeYearManager
from .managers.countryyear import CountryYearManager


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


class CountryYear(models.Model):
    year = models.IntegerField(blank=True, null=True)
    country = models.CharField(blank=True, max_length=2)
    total = models.FloatField(default=0.0)

    class Meta:
        db_table = 'data_countryyear'
        get_latest_by = 'year'
        ordering = ('year',)

    objects = CountryYearManager()


class Recipient(models.Model):
    recipientid = models.CharField(max_length=10)
    recipientidx = models.CharField(max_length=10, null=True)
    globalrecipientid = models.CharField(primary_key=True, max_length=10)
    globalrecipientidx = models.CharField(max_length=10)
    name = models.TextField(null=True)
    address1 = models.TextField(blank=True, null=True)
    address2 = models.TextField(blank=True, null=True)
    zipcode = models.CharField(max_length=100, blank=True, null=True)
    town = models.TextField(blank=True, null=True)
    countryrecipient = models.CharField(blank=True,
            max_length=2, null=True, db_index=True)
    countrypayment = models.CharField(max_length=2,
            blank=True, null=True, db_index=True)
    geo1 = models.TextField(blank=True, null=True)
    geo2 = models.TextField(blank=True, null=True)
    geo3 = models.TextField(blank=True, null=True)
    geo4 = models.TextField(blank=True, null=True)
    geo1nationallanguage = models.TextField(blank=True, null=True)
    geo2nationallanguage = models.TextField(blank=True, null=True)
    geo3nationallanguage = models.TextField(blank=True, null=True)
    geo4nationallanguage = models.TextField(blank=True, null=True)
    lat = models.FloatField(blank=True, null=True, default=None)
    lng = models.FloatField(blank=True, null=True, default=None)
    total = models.FloatField(default=0.0, null=True, db_index=True)

    objects = RecipientManager()

    def __str__(self):
        return "%s (%s)" % (self.pk, self.name)

    class Meta:
        db_table = 'data_recipient'
        ordering = ('-total',)

    def get_absolute_url(self):
        return reverse('recipient_view',
            args=[self.countrypayment, self.pk, slugify(self.name)])


class RecipientYear(models.Model):
    """
    Denormalized model containing the total each recipient received per year.
    """
    recipient = models.ForeignKey('Recipient', on_delete=models.CASCADE)
    name = models.TextField(null=True)
    year = models.IntegerField(blank=True, null=True)
    country = models.CharField(blank=True, max_length=2)
    total = models.FloatField(default=0.0, null=True, db_index=True)

    objects = RecipientYearManager()

    class Meta:
        db_table = 'data_recipientyear'
        ordering = ('-total',)

    def get_absolute_url(self):
        return reverse('recipient_view', args=[self.country, self.recipient_id, slugify(self.name)])


class Payment(models.Model):
    paymentid = models.TextField()
    globalpaymentid = models.CharField(max_length=10, primary_key=True)
    recipient = models.ForeignKey(Recipient, db_column='globalrecipientid',
                                  max_length=10,
                                  on_delete=models.CASCADE)
    globalrecipientidx = models.CharField(max_length=10, db_index=True)
    scheme = models.ForeignKey('Scheme', db_column='globalschemeid', on_delete=models.CASCADE)
    amounteuro = models.FloatField(null=True, db_index=True)  # This field type is a guess.
    amountnationalcurrency = models.FloatField(null=True)  # This field type is a guess.
    year = models.IntegerField(db_index=True)
    countrypayment = models.CharField(max_length=4, default=None, db_index=True)

    class Meta:
        db_table = 'data_payment'


class Scheme(models.Model):
    globalschemeid = models.CharField(max_length=40, primary_key=True)
    namenationallanguage = models.TextField(null=True)
    nameenglish = models.TextField(db_index=True)
    budgetlines8digit = models.CharField(max_length=10, null=True)
    countrypayment = models.CharField(max_length=2)
    total = models.FloatField(null=True, default=0.0)

    objects = SchemeManager()

    class Meta:
        db_table = 'data_scheme'

    def __str__(self):
        return "%s - %s" % (self.pk, self.nameenglish)

    def get_absolute_url(self):
        return reverse('scheme_view', args=[self.countrypayment,
                                            self.pk,
                                            slugify(self.nameenglish)])


class SchemeYear(models.Model):
    globalschemeid = models.ForeignKey(Scheme, db_column='globalschemeid', on_delete=models.CASCADE)
    nameenglish = models.TextField(blank=True)
    countrypayment = models.CharField(blank=True, max_length=2)
    year = models.IntegerField(blank=True, null=True)
    total = models.FloatField(null=True, default=0.0)

    objects = SchemeYearManager()

    class Meta:
        db_table = 'data_schemeyear'
        ordering = ('year',)

    def get_absolute_url(self):
        return reverse('scheme_view', args=[self.countrypayment,
                                            self.globalschemeid_id,
                                            slugify(self.nameenglish)])


class RecipientSchemeYear(models.Model):
    """
    Denormalized data, containing the sum of the payments to each recipient in a
    year, including '0' for all years
    """
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE)
    country = models.CharField(blank=True, max_length=2)
    year = models.IntegerField(blank=True, null=True)
    total = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return u"%s - %s" (self.recipient, self.year)

    class Meta:
        db_table = 'data_recipientschemeyear'
        ordering = ('-total',)

    def get_absolute_url(self):
        return reverse('recipient_view', args=[self.country, self.recipient_id, slugify(self.recipient.name)])


# class SchemeType(models.Model):
#     """
#     Model for defining what broad category a scheme fits in to.
#
#     See the "scheme_types" managment command for how this is populated.
#     """
#     DIRECT = 0
#     INDIRECT = 1
#     RURAL = 2
#
#     SCHEME_TYPES = (
#         (DIRECT, 'Direct'),
#         (INDIRECT, 'Indirect'),
#         (RURAL, 'Rural'),
#     )
#
#     globalschemeid = models.ForeignKey(Scheme, primary_key=True)
#     country = models.CharField(blank=False, max_length=2,
#         choices=countries.items())
#     scheme_type = models.IntegerField(choices=SCHEME_TYPES)
#
#     def __unicode__(self):
#         return "%s - %s" % (self.globalschemeid, self.scheme_type)


class TotalYear(models.Model):
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE)
    year = models.IntegerField(blank=True, null=True, db_index=True)
    total = models.FloatField(null=True, default=0.0, db_index=True)
    country = models.CharField(blank=False, max_length=2)

    class Meta:
        db_table = 'data_totalyear'
        ordering = ('-total',)


# class Location(MP_Node):
#     geo_type = models.CharField(blank=True, max_length=10)
#     name = models.CharField(max_length=255)
#     slug = models.SlugField(max_length=255)
#     country = models.CharField(blank=True, max_length=100)
#     recipients = models.IntegerField(blank=True, null=True)
#     total = models.FloatField(null=True, default=0.0)
#     average = models.FloatField()
#     lat = models.FloatField(null=True)
#     lon = models.FloatField(null=True)
#     year = models.IntegerField(blank=True, null=True, db_index=True)
#
#     def __unicode__(self):
#         return self.name
#
#     def get_absolute_url(self):
#         return reverse('location_view', args=[self.country, self.year, self.slug])
