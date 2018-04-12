# encoding: utf-8
from django.db import models
from django.db.models import Sum


class SchemeManager(models.Manager):
    """
    Various reusable queries, like top_schemes
    """

    def get_queryset(self):
        return super(SchemeManager, self).get_queryset().filter(
                total__isnull=False)

    def top_schemes(self, country=None, limit=10):
        """
        Top schemes for a given country over all years.
        """
        kwargs = {}
        if country and country != "EU":
            kwargs['countrypayment'] = country

        schemes = self.get_queryset().filter(**kwargs).order_by('-total')
        return schemes[:limit]


class SchemeYearManager(models.Manager):
    """
    Various reusable queries, like top_schemes
    """

    def get_queryset(self):
        return super(SchemeYearManager, self).get_queryset().filter(
                total__isnull=False)

    def top_schemes(self, country=None, year=None):
        kwargs = {}

        if year is not None:
            kwargs['year'] = year

        if country and country != "EU":
            kwargs['countrypayment'] = country

        schemes = (self.get_queryset()
            .filter(**kwargs)
            .select_related('globalschemeid')
            .annotate(scheme_total=Sum('total'))
            .order_by('-scheme_total'))
        return schemes
