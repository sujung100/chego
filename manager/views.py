from django.shortcuts import render, redirect, get_object_or_404
from reservation import models as rsv

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView
from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect

from django.http import JsonResponse, QueryDict, HttpRequest
from django.views import View
from django.core.paginator import Paginator



# Create your views here.
def store_list(request):
    return render(request, "manager/manager_index.html")

class ManagerStoreList(LoginRequiredMixin, ListView, LoginView, FormView):
    model = rsv.Store
    template_name = "manager/manager_index.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("index")
    login_url = reverse_lazy("login")

    def get_queryset(self):
        current_user = self.request.user
        if current_user.is_authenticated:
            manager = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)[:3]
        else:
            manager = rsv.Store.objects.none()
        return manager

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = self.request.user

        context['manager'] = self.get_queryset()
        print(context['manager'])
         # QuerySet to list of dicts.
        manager_list_dicts = [model_to_dict(manager) for manager in self.get_queryset()]
        
        # List of dicts to JSON string.
        context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)

        if current_user.is_authenticated:
            rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
            context["rsvs"] = rsvs
        return context
    
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.method == 'POST':
                print("안돼야 되잖아")
                sto = rsv.Store()
                # print(atc.title)
                sto.store_name = request.POST["store_name"]
                sto.address = request.POST["address"]
                sto.owner = request.user
                sto.save()

                
                selectTime = request.POST.getlist("select_time[]")
                for time in selectTime:
                    # print(time)
                    sts = rsv.Store_times()
                    sts.store_id = sto
                    sts.reservation_time = time
                    sts.save()
                
                # POST 처리 완료 시 리디렉션
                return HttpResponseRedirect(self.success_url)
            

        return self.get(request, *args, **kwargs)
    
  
# class StoreTimesView(View):
#     def get(self, request: HttpRequest):
#         current_user = request.user

#         if current_user.is_authenticated:
#             # Get the stores owned by the user
#             stores = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)[:3]

#             # Get the 'store_id' query parameter from the GET request
#             query_dict = QueryDict(request.META['QUERY_STRING'])
#             requested_store_id = query_dict.get('store_id', None)

#             # Get the store times for each store
#             data = []
#             for store in stores:
#                 if requested_store_id is not None and str(store.id) != requested_store_id:
#                     continue
                
#                 rsv_users = rsv.Reservation_user.objects.filter(store_id=store)
#                 data.append([model_to_dict(rsv_user) for rsv_user in rsv_users])

#             return JsonResponse(data, safe=False)
#         else:
#             return JsonResponse([], safe=False)

class StoreTimesView(View):
    def get(self, request):
        current_user = request.user

        if current_user.is_authenticated:
            stores = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)[:3]

            query_dict = QueryDict(request.META['QUERY_STRING'])
            requested_store_id = query_dict.get('store_id', None)

            data = []
            for store in stores:
                if requested_store_id is not None and str(store.id) != requested_store_id:
                    continue
                
                rsv_users = rsv.Reservation_user.objects.filter(store_id=store)
                data.append([model_to_dict(rsv_user) for rsv_user in rsv_users])

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse([], safe=False)
    

# class ManagerStoreList(LoginRequiredMixin, ListView):
#     model = rsv.Store
#     template_name = "manager/manager_index.html"

#     def get_queryset(self):
#         current_user = self.request.user
#         manager = rsv.Store.objects.filter(owner=current_user)
#         return manager

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['manager'] = self.get_queryset()
#         return context

def detail_list(request, store_id):
    store = get_object_or_404(rsv.Store, id=store_id)
    store_time = rsv.Store_times.objects.filter(store_id=store_id)
    user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

    user_dates = []
    dates_list = [date.reservation_date for date in user_time]
    print(dates_list)
    user_dates.append({
        "user_dates" : dates_list
    })
    context = {"user_dates_json" : json.dumps(dates_list, cls=DjangoJSONEncoder)}


    return render(request, "manager/manager_store_detail.html", context)
    
class UserSignUpView(CreateView):
    form_class = UserCreationForm
    template_name = "manager/manager_sign_up.html"
    success_url = reverse_lazy("signup_done")

    # def form_valid(self, form):
    #     valid = super().form_valid(form)
    #     login(self.request, self.object)  # 로그인 후 바로 로그인 상태로 만드는 부분
    #     return valid

    def form_valid(self, form):
        user = form.save(commit=False)
        # 필요한 처리 수행
        user.save()

        # Create Manager instance
        manager, created = rsv.Manager.objects.get_or_create(user=user)

        if not created:
            form.add_error(None, ValidationError('User ID 중복입니다.'))

        # 이 부분을 created 조건과 분리하고 두 경우 모두에서 실행되도록 함.
        manager.manager_name = self.request.POST['username']
        manager.manager_phone = self.request.POST['phone_number']
        manager.save()

        # if not created:
        #     return self.form_invalid(form)

        # login(self.request, user)

        return redirect(self.success_url)
    
    
class UserCreateDoneTV(TemplateView):
    template_name = "manager/sign_up_done.html"

class UserLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = "manager/manager_login.html"
    success_url = reverse_lazy("index")  
    # 원하는 인덱스 페이지 이름을 사용하십시오.

def write(request):
   
    if request.method == 'POST':
        sto = rsv.Store()
        # print(atc.title)
        sto.store_name = request.POST["store_name"]
        sto.address = request.POST["address"]
        sto.owner = request.user
        sto.save()

        
        selectTime = request.POST.getlist("select_time[]")
        for time in selectTime:
            # print(time)
            sts = rsv.Store_times()
            sts.store_id = sto
            sts.reservation_time = time
            sts.save()
    
    return render(request, 'manager/manager_write.html')


def test_chat(request):
    return render(request, "manager/test/test_chat.html")

def test_room(request, room_name):
    return render(request, "manager/test/test_room.html", {"room_name": room_name})

