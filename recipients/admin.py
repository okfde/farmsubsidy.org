from django.contrib import admin

from .models import (CountryYear, Payment, Recipient, RecipientSchemeYear,
    RecipientYear, Scheme, SchemeYear)


class RecipientAdmin(admin.ModelAdmin):
    search_fields = ['=globalrecipientid', 'name']
    list_display = ('recipientid', 'globalrecipientid', 'name', 'zipcode', 'town', 'countryrecipient', 'website')
    list_filter = ('countryrecipient',)
    actions = ['remove_from_index']

    def remove_from_index(self, request, queryset):
        from haystack import connections as haystack_connections

        for recipient in queryset:
            for using in haystack_connections.connections_info.keys():
                backend = haystack_connections[using].get_backend()
                backend.remove(recipient)

        self.message_user(request, "Removed from search index")
    remove_from_index.short_description = "Remove from search index"

    def website(self, instance):
        return '<a href="' + instance.get_absolute_url() + '" target="_blank">Link</a>'
    website.allow_tags = True


class SchemeAdmin(admin.ModelAdmin):
    search_fields = ['=globalschemeid', 'namenationallanguage', 'nameenglish']
    list_display = ('globalschemeid', 'namenationallanguage', 'nameenglish', 'countrypayment', 'total', 'website',)
    list_filter = ('countrypayment',)

    def website(self, instance):
        return '<a href="' + instance.get_absolute_url() + '" target="_blank">Link</a>'
    website.allow_tags = True


class PaymentAdmin(admin.ModelAdmin):
    search_fields = ['=globalpaymentid']
    list_display = ('globalpaymentid', 'globalrecipientidx', 'scheme', 'amounteuro', 'amountnationalcurrency', 'year', 'countrypayment')
    list_filter = ('countrypayment',)


class CountryYearAdmin(admin.ModelAdmin):
    list_display = ('year', 'country', 'total',)
    list_filter = ('year', 'country',)


class RecipientYearAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'year', 'country', 'total',)
    list_filter = ('year', 'country',)


class SchemeYearAdmin(admin.ModelAdmin):
    search_fields = ['=globalschemeid']
    list_display = ('globalschemeid', 'nameenglish', 'countrypayment', 'year', 'total',)
    list_filter = ('countrypayment', 'year',)


class RecipientSchemeYearAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'scheme', 'country', 'year', 'total',)
    list_filter = ('country', 'year',)


admin.site.register(Recipient, RecipientAdmin)
admin.site.register(Scheme, SchemeAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(CountryYear, CountryYearAdmin)
admin.site.register(RecipientYear, RecipientYearAdmin)
admin.site.register(SchemeYear, SchemeYearAdmin)
admin.site.register(RecipientSchemeYear, RecipientSchemeYearAdmin)


# # admin.site.register(FeedItems, FeedItemsAdmin)
# # admin.site.register(FeedCategories)
