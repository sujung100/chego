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
# Create your views here.


class Idx_list(ListView):
    model = models.Store
    template_name = "reservation/index.html"
# def Idx(request):
#     return render(request,"index.html")

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
    sto = get_object_or_404(models.Store, pk=pk)
    context = {"store":sto}
    return render(request,"reservation/detail.html",context)

def list_up(request):
    return render(request, "listup.html")

def reserve(request):
    return render(request, "reservation.html")