from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
# from django_tutorial.views import OOM
from . import models

# from community.forms import Form
# from community.models import Article, Select_times, Article_user

import sqlite3
from django.db.models import Q
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required

from django.http import JsonResponse
from django.core import serializers
# Create your views here.


# class Idx_list(ListView):
#     model = models.Store
#     template_name = "reservation/index.html"
# # def Idx(request):
# #     return render(request,"index.html")

def write(request):
   
    if request.method == 'POST':
        sto = models.Store()
        # print(atc.title)
        sto.store_name = request.POST["store_name"]
        sto.address = request.POST["address"]
        # sto.owner = request.user
        sto.save()

        
        selectTime = request.POST.getlist("select_time[]")
        for time in selectTime:
            # print(time)
            sts = models.Store_times()
            sts.store_id = sto
            sts.reservation_time = time
            sts.save()
    
    return render(request, 'reservation/write.html')

def detail(request,pk):
    print("왜안되냐")
    sto = get_object_or_404(models.Store, pk=pk)
    sto_time = models.Store_times.objects.filter(store_id=pk)

    if request.method == 'POST':
        
        rst_user = models.Reservation_user()
        rst_user.user_name = request.POST["detail_user_name"]
        rst_user.user_phone = request.POST["detail_user_phone"]
        rst_user.reservation_date = request.POST["detail_user_date"]
        rst_user.user_time = request.POST["detail_user_time"]
        rst_user.store_id = sto
        rst_user.save()

    store_dates = []
    for dates in sto_time:
        dates_info  = models.Reservation_user.objects.filter(
            Q(store_id=sto) &
            Q(user_time=dates.reservation_time) 
        )
      
        user_dates = [info.reservation_date for info in dates_info]
        store_dates.append({
            'user_date': user_dates,
            'disable_time': json.dumps([info.user_time for info in dates_info ])
        })
    context = {"store":sto, "sto_time":sto_time,
               "store_dates_json": json.dumps(store_dates, cls=DjangoJSONEncoder),}
    return render(request,"reservation/reserve.html",context)

def list_up(request):
    return render(request, "listup.html")

def reserve(request):
    return render(request, "reservation.html")