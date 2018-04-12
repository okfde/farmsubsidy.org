# encoding: utf-8
from django.db import models


class RecipientManager(models.Manager):
    """
    Various reusable queries, like top_recipients
    """

    def top_recipients(self, country=None, year=0):
        recipients = self.all().filter(total__isnull=False)
        recipients = recipients
        kwargs = {}
        if country and country != 'EU':
            kwargs['countrypayment'] = country
        if int(year) != 0:
            kwargs['payment__year__exact'] = year
        recipients = recipients.filter(**kwargs)
        return recipients.order_by('-total')

    def recipents_for_location(self, location, country='EU'):
        """
        Given a location slug, retuen all recipients where the geo fields match.

        Location slugs are paths like a/b/c, where a=geo1, b=geo2 etc.

        Because we have the RecipientYear model, every total returned here is
        for all years
        """

        geos = []
        for l in location.get_ancestors():
            geos.append(l)
        geos.append(location)
        kwargs = {}
        for i, g in enumerate(geos):
            i = i + 1
            kwargs["geo%s" % i] = g.name

        qs = self.filter(**kwargs)
        # qs = qs.only('name', 'total', 'countrypayment',)
        return qs
