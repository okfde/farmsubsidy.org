from django.core.paginator import Paginator as oPaginator
from django.core.paginator import Page as oPage


class Paginator(oPaginator):
    def __init__(self, object_list, per_page, orphans=0,
                allow_empty_first_page=True, where_names=['total', 'globalrecipientid'], where_list=[]):
        self.object_list = object_list
        self.per_page = per_page
        self.orphans = orphans
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None
        self.where_list = where_list
        self.where_names = where_names

    def page(self, number, start):
        "Returns a Page object for the given 1-based page number."
        self.where_list = start.split('-')

        number = self.validate_number(number)
        bottom = 0
        top = self.per_page

        qs_slice = self.object_list

        if len(self.where_list) == len(self.where_names):
            where_names = ",".join(self.where_names)
            where_list = ",".join("'%s'" % i for i in self.where_list)
            qs_slice = qs_slice.extra(where=["(%s) <= (%s)" % (where_names, where_list)])
            back_slice = self.object_list.extra(where=["(%s) >= (%s)" % (where_names, where_list)])
            back_slice = list(back_slice.reverse())
        else:
            qs_slice = qs_slice
            back_slice = qs_slice[:self.per_page]
            back_slice = list(reversed(back_slice))

        if number == 1:
            self.previous_obj = None
        else:
            try:
                self.previous_obj = back_slice[top]
            except IndexError:
                self.previous_obj = back_slice[-1]
        try:
            self.next_obj = qs_slice[top]
        except IndexError:
            self.next_obj = None

        qs_slice = qs_slice[bottom:top]

        return Page(qs_slice, number, self)


class Page(oPage):
    def format_next_link(self):
        obj = self.paginator.next_obj
        number = self.number + 1
        return "?page=%s&start=%s-%s" % (number, obj.total, obj.pk)

    def format_previous_link(self):
        obj = self.paginator.previous_obj
        number = self.number - 1
        return "?page=%s&start=%s-%s" % (number, obj.total, obj.pk)
