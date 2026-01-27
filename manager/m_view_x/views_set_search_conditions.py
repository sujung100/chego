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
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.db.models import Q

from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

import json
from .forms import ManagerUpdateForm, StoreUpdateForm, UpdateForm

from datetime import datetime

# 검색기능 - 전화번호 조회시 기호제거
from django.db.models import F, Func, Value, CharField
from django.db.models.functions import Replace



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
        context['manager'] = self.manager
        context['store'] = self.store

        kw = self.request.GET.get('kw')
        if kw:
            try:
                # 'YYYY-MM-DD' 형식의 문자열을 날짜로 변환
                datetime.strptime(kw, '%Y-%m-%d')
                date_filter = Q(reservation_date__icontains=kw)
            except ValueError:
                try:
                    # 'YYYY-MM' 형식의 문자열을 날짜로 변환
                    datetime.strptime(kw, '%Y-%m')
                    date_filter = Q(reservation_date__icontains=kw)
                except ValueError:
                    date_filter = Q(reservation_date__startswith=kw)  # 수정: startswith 사용
                    
            # 입력에서 이름과 전화번호 또는 예약일 분리
            if ',' in kw:
                condition1, condition2 = [x.strip() for x in kw.split(',', 1)]
                condition1_without_hyphen = condition1.replace("-", "")
                condition2_without_hyphen = condition2.replace("-", "")

                # 이름과 전화번호, 이름과 예약일, 전화번호와 예약일 모두 만족하는 결과 반환
                reservations = Reservation_user.objects.annotate(
                    user_phone_without_hyphen=Replace('user_phone', Value('-'), Value(''), output_field=CharField())
                ).filter(
                    (
                        (Q(user_name__icontains=condition1) & Q(user_phone_without_hyphen__icontains=condition2_without_hyphen)) |
                        (Q(user_name__icontains=condition1) & Q(reservation_date__iexact=condition2)) |
                        (Q(user_phone_without_hyphen__icontains=condition1_without_hyphen) & Q(reservation_date__iexact=condition2))
                    ),
                    store_id=self.store
                ).distinct()
            else:
                name_or_phone_or_date = kw.replace("-", "")

                reservations = Reservation_user.objects.annotate(
                    user_phone_without_hyphen=Replace('user_phone', Value('-'), Value(''), output_field=CharField())
                ).filter(
                    Q(user_name__icontains=name_or_phone_or_date) |  # OR 연산자 사용
                    Q(user_phone_without_hyphen__icontains=name_or_phone_or_date) |
                    Q(reservation_date__iexact=name_or_phone_or_date),
                    store_id=self.store
                ).distinct()
        else:
            reservations = Reservation_user.objects.filter(
                store_id=self.store  # store_id가 현재 스토어의 ID와 같을때만 검색해서 조회가능
            )


        paginator = Paginator(reservations, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['kw'] = kw  # 검색어를 context에 추가

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




# 수정중
class Update(LoginRequiredMixin, UpdateView):
    model = rsv.Store
    form_class = UpdateForm
    template_name = 'manager/manager_update_form.html'


    # 권한설정
    def dispatch(self, request, *args, **kwargs):
        self.manager = get_object_or_404(Manager, pk=kwargs['pk'])
        self.store = get_object_or_404(Store, pk=kwargs['store_id'])
        
        # 조건3개
        if request.user.is_authenticated and request.user == self.manager.user and self.manager.user == self.store.owner:
            return super(Update, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # URL에서 store_id값 가져오기
        requested_store_id = self.kwargs.get('store_id')

        # 해당 store_id를 가진 Store 객체 찾기
        store = get_object_or_404(rsv.Store, pk=requested_store_id)

        if store:
            context['store'] = store

            # Store의 owner(User 객체)와 연결된 Manager 찾기
            manager_of_the_store = Manager.objects.filter(user=store.owner).first()
            
            if manager_of_the_store:
                context['manager'] = manager_of_the_store

            sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk)
            context['sto_time_objects'] = sto_time_objects
            
            sto_time_values_list  = {
                'store_id': store.pk,
                'sto_time': list(sto_time_objects.values()),
            }

            print()
            print("이거 찍어봐: ", sto_time_values_list)
            print()
             # 예약 정보 가져오기 
            disabled_dates_info_list = []
            for sto_time in sto_time_objects:
                reservation_user_objects = rsv.Reservation_user.objects.filter(
                    Q(store_id=store) &
                    Q(user_time=sto_time.reservation_time)
                )

                if reservation_user_objects.exists():  # Add this line
                    hour_disabled_dates_dict = {}

                    for reservation in reservation_user_objects:
                        user_date_str = reservation.reservation_date
                                
                        datetime_obj = datetime.strptime(reservation.user_time, '%H:%M')
                        formatted_time_str = datetime_obj.strftime('%H:%M')

                        if user_date_str not in hour_disabled_dates_dict:
                            hour_disabled_dates_dict[user_date_str] = []

                        hour_disabled_dates_dict[user_date_str].append(formatted_time_str)

                    disabled_dates_info_list.append({
                        'hour_disabled_dates': hour_disabled_dates_dict,
                        'user_date': [info.reservation_date for info in reservation_user_objects],
                        'disable_time': [datetime.strptime(info.user_time, '%H:%M').strftime("%H:%M") for info in reservation_user_objects]
                    })

            context['disabled_dates_info_json'] = json.dumps(disabled_dates_info_list , cls=DjangoJSONEncoder)
        print(context['disabled_dates_info_json'])

        return context

    
