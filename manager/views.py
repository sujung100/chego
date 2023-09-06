from django.shortcuts import render, redirect,  get_object_or_404
from calendar_app import models as rsv
from calendar_app.models import Manager, Store,  Reservation_user

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, ListView, UpdateView, FormView
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Q

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

import json
from .forms import ManagerUpdateForm, StoreUpdateForm, UpdateForm




# 임시
# from django.views.generic.edit import FormView
# from calendar_app.models import Manager, Store,  Reservation_user
# from .forms import ManagerUpdateForm, StoreUpdateForm
# from django.urls import reverse_lazy, reverse
# from django.shortcuts import get_object_or_404
# from django.core.exceptions import PermissionDenied
# from django.http import HttpResponseRedirect


# Create your views here.
# def store_list(request):
#     return render(request, "manager/manager_index.html")

class ManagerStoreList(ListView):
    model = rsv.Store
    template_name = "manager/manager_index.html"

    def get_queryset(self):
        current_user = self.request.user
        if current_user.is_authenticated:
            manager = rsv.Store.objects.filter(owner=current_user)
        else:
            manager = rsv.Store.objects.none()
        return manager

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['manager'] = self.get_queryset()
        return context
    
# test중 - 삭제예정
# class ManagerStoreList(ListView):
#     model = rsv.Store

#     def dispatch(self, request, *args, **kwargs):
#         template_choice = kwargs.get('template_choice', '')
#         if template_choice == '':
#             self.template_name = 'manager/manager_index.html'
#         elif template_choice == 'operate':
#             self.template_name = 'manager/manager_operate.html'
#         return super().dispatch(request, *args, **kwargs)

#     def get_queryset(self):
#         current_user = self.request.user
#         if current_user.is_authenticated:
#             manager = rsv.Store.objects.filter(owner=current_user)
#         else:
#             manager = rsv.Store.objects.none()
#         return manager

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['manager'] = self.get_queryset()
#         return context
    


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
    success_url = reverse_lazy("index")  # 원하는 인덱스 페이지 이름을 사용하십시오.

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

# 참고
# @login_required(login_url='common:login')
# def operate(request):
#     question = get_object_or_404(Question, pk=question_id)
#     if request.user != question.author:
#         messages.error(request, '수정권한이 없습니다')
#         return redirect('pybo:detail', question_id=question.id)
#     if request.method == "POST":
#         form = QuestionForm(request.POST, instance=question)
#         if form.is_valid():
#             question = form.save(commit=False)
#             question.modify_date = timezone.now()  # 수정일시 저장
#             question.save()
#             return redirect('pybo:detail', question_id=question.id)
#     else:
#         form = QuestionForm(instance=question)
#     context = {'form': form}
#     return render(request, 'manager/manager_operate.html', context)

# @login_required(login_url='common:login')
# def operate(request):
#     return render(request, 'manager/manager_operate.html')


# 접근/수정 권한 설정
# class ManagerUpdateList(LoginRequiredMixin, UpdateView):
#     model = rsv.Manager
#     form_class = ManagerUpdateForm
#     template_name = 'manager/manager_operate.html'

#     def form_valid(self, form):
#         response = super(ManagerUpdateList, self).form_valid(form)
#         return response

#     def dispatch(self, request, *args, **kwargs):
#         if request.user.is_authenticated and request.user == self.get_object().user:
#             return super(ManagerUpdateList, self).dispatch(request, *args, **kwargs)
#         else:
#             raise PermissionDenied





class ManagerStoreUpdateView(LoginRequiredMixin, FormView):
    template_name = 'manager/manager_operate.html'
    form_class = ManagerUpdateForm
    store_form_class = StoreUpdateForm

    # 권한설정
    def dispatch(self, request, *args, **kwargs):
        self.manager = get_object_or_404(Manager, pk=kwargs['pk'])
        self.store = get_object_or_404(Store, pk=kwargs['store_id'])
        
        # 조건3개
        if request.user.is_authenticated and request.user == self.manager.user and self.manager.user == self.store.owner:
            return super(ManagerStoreUpdateView, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, **kwargs):
        context = super(ManagerStoreUpdateView, self).get_context_data(**kwargs)
        context['form'] = ManagerUpdateForm(instance=self.manager)
        context['form_store'] = StoreUpdateForm(instance=self.store)

        # 예약목록 가져오기
        reservations = Reservation_user.objects.filter(store_id=self.store)
        context['reservations'] = reservations
        return context

    def form_valid(self, form):
        manager_form = form
        store_form = self.store_form_class(self.request.POST, instance=self.store)

        if manager_form.is_valid() and store_form.is_valid():
            manager_form.save()
            store_form.save()
            return HttpResponseRedirect(reverse('success_page'))
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = super(ManagerStoreUpdateView, self).get_context_data()
        context['form'] = form
        context['form_store'] = self.store_form_class(self.request.POST, instance=self.store)
        return self.render_to_response(context)



# def Update(request):
#     return render (request, 'manager/manager_update_form.html')


# 주석..//새로만들자
# class Update(LoginRequiredMixin, UpdateView):
#     model = rsv.Store
#     form_class = UpdateForm
#     template_name = 'manager/manager_update_form.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         store_list = rsv.Store.objects.all()

#         # URL에서 store_id값 가져오기
#         requested_store_id = self.kwargs.get('store_id')

#         # store.pk값이 있는 상점만 필터링
#         filtered_store_list = [store for store in store_list if store.pk == requested_store_id]
#         context['store_list'] = filtered_store_list

#         store_times_dict = {}
#         for store in filtered_store_list: # 필터링된 목록사용
#             store_times = rsv.Store_times.objects.filter(store_id=store.pk)
#             store_times_dict[store.pk] = store_times
#         context['store_times_dict'] = store_times_dict

        
#         store_data = []
        
#         for store in filtered_store_list: # 필터링된 목록사용
#             sto_time = rsv.Store_times.objects.filter(store_id=store.pk)
#             store_dates = []
#             for dates in sto_time:
#                 dates_info  = rsv.Reservation_user.objects.filter(
#                 Q(store_id=store) &
#                 Q(user_time=dates.reservation_time) 
#                 )

#                 hour_disabled_dates = {}

#                 for res in dates_info:
#                     user_date = res.reservation_date
#                     user_time = res.user_time

#                     # 일부 예약이 이미 비활성 시간에 추가된 경우 해당 시간을 추가하고, 그렇지 않은 경우 새로운 항목을 만듭니다.
#                     if user_date in hour_disabled_dates:
#                         hour_disabled_dates[user_date].append(user_time)
#                     else:
#                         hour_disabled_dates[user_date] = [user_time]

#                 user_dates = [info.reservation_date for info in dates_info]
#                 store_dates.append({                                  # 수정된 위치의 append() 호출
#                     'hour_disabled_dates': hour_disabled_dates,
#                     'user_date': user_dates,
#                     'disable_time': json.dumps([info.user_time for info in dates_info])
#                 })
#                 # print(store_dates)
#             store_data.append({
#                 'store_id': store.pk,
#                 'sto_time': list(sto_time.values()),
#                 'store_dates_json': json.dumps(store_dates, cls=DjangoJSONEncoder),
#             })

#         # context['store_data'] = store_data
#         context['store_data_json'] = json.dumps(store_data, cls=DjangoJSONEncoder)
#         # print(store_data)
#         return context
    


class Update(LoginRequiredMixin, UpdateView):
    model = rsv.Store
    form_class = UpdateForm
    template_name = 'manager/manager_update_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_list = rsv.Store.objects.all()

        # URL에서 store_id값 가져오기
        requested_store_id = self.kwargs.get('store_id')

        # store.pk값이 있는 상점만 필터링
        filtered_store_list = [store for store in store_list if store.pk == requested_store_id]
        context['store_list'] = filtered_store_list

        store_times_dict = {}
        for store in filtered_store_list: # 필터링된 목록사용
            store_times = rsv.Store_times.objects.filter(store_id=store.pk)
            store_times_dict[store.pk] = store_times
        context['store_times_dict'] = store_times_dict

        push_val = self.request.COOKIES.get('push_val', None)
        print("쿠키 데이터 : ", push_val)
        push_val2 = self.request.COOKIES.get('push_val2', None)
        print("쿠키 데이터2 : ", push_val2)
        input_val = self.request.COOKIES.get('input_val', None)
        print("쿠키 데이터3 : ", input_val)
        store_data = []
        
        for store in filtered_store_list: # 필터링된 목록사용
            sto_time = rsv.Store_times.objects.filter(store_id=store.pk)
            store_data.append({
                'store_id': store.pk,
                'sto_time': list(sto_time.values()),
            })
        return context