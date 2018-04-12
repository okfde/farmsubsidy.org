# encoding: utf-8
from django.db import models


class CountryYearManager(models.Manager):
    """
    Various reusable queries, like top_schemes
    """

    def get_queryset(self):
        return super(CountryYearManager, self).get_queryset().filter(
                total__isnull=False)

    def year_max_min(self, country=None):
        """
        return a tuple of the highest and lowest year know about for a country
        """
        kwargs = {}
        if country and country != "EU":
            kwargs['country'] = country

        years = self.get_queryset().filter(**kwargs)\
                .order_by('-year').values('year')
        years = [y['year'] for y in years]
        if not years:
            # If no years, return a 'blank' list
            years = [0, 0]

        return min(years), max(years)
