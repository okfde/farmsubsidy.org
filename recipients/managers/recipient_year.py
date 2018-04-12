# encoding: utf-8
from django.db import models


class RecipientYearManager(models.Manager):
    """
    Various reusable queries, like top_recipients
    """

    def get_queryset(self):
        return super(RecipientYearManager, self).get_queryset().filter(
                total__isnull=False)

    def recipents_for_location(self, location, year=None, country='EU'):
        """
        Given a location slug, retuen all recipients where the geo fields match.

        Location slugs are paths like a/b/c, where a=geo1, b-geo2 etc.

        """

        geos = []
        for l in location.get_ancestors():
            geos.append(l)
        geos.append(location)

        kwargs = {}
        for i, g in enumerate(geos):
            i = i + 1
            kwargs["recipient__geo%s" % i] = g.name

        if country != 'EU':
            kwargs['country'] = country
            kwargs['recipient__countrypayment'] = country

        if year is not None:
            kwargs['year'] = year

        qs = self.get_queryset().filter(**kwargs)
        # qs = qs.only('name', 'total', 'country',)
        return qs
