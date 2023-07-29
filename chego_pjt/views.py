from django.shortcuts import render
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from reservation import models


class Idx_list(ListView):
    model = models.Store
    template_name = "reservation/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_list = context['object_list']

        # print(store_list)
        # Fetch Store_times for each store
        store_times_dict = {}
        store_time_date = []
        for store in store_list:
            store_times = models.Store_times.objects.filter(store_id=store.pk)
            store_times_dict[store.pk] = store_times

        # for date in store_times:



        context['store_times_dict'] = store_times_dict
        return context



def Idx(request):
    return render(request,"reservation/index.html")