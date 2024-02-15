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


        name = self.request.GET.get('name')
        phone = self.request.GET.get('phone')
        kw = self.request.GET.get('kw')
        
        date_filter = Q()
        if kw:
            try:
                datetime.strptime(kw, '%Y-%m-%d')
                date_filter = Q(reservation_date__icontains=kw)
            except ValueError:
                try:
                    datetime.strptime(kw, '%Y-%m')
                    date_filter = Q(reservation_date__icontains=kw)
                except ValueError:
                    date_filter = Q(reservation_date__startswith=kw)
                    
        phone_without_hyphen = phone.replace("-", "") if phone else None

        reservations = Reservation_user.objects.annotate(
            user_phone_without_hyphen=Replace('user_phone', Value('-'), Value(''), output_field=CharField())
        ).filter(
            Q(user_name__icontains=name) if name else Q(),
            Q(user_phone_without_hyphen__icontains=phone_without_hyphen) if phone else Q(),
            date_filter if kw else Q(),
            store_id=self.store
        ).distinct()

        paginator = Paginator(reservations, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['kw'] = kw

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

    # 임시...테스트용 form_vaild검증 없이 그냥 post요청 들어오면 update_data함수 실행되도록함..
    # def post(self, request, *args, **kwargs):
    #     self.update_data(request, **kwargs)  # update_data 함수 호출
    #     return super().post(request, *args, **kwargs)  # 원래 post 함수 호출
    
    # 얘도 임시...나중 수정하기
    # def get_object(self, queryset=None):
    #     requested_store_id = self.kwargs.get('store_id')
    #     return get_object_or_404(rsv.Store, pk=requested_store_id)


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
        # print("찍어보자1", requested_store_id)

        # 해당 store_id를 가진 Store 객체 찾기
        # Store테이블의 id값찾기 (url에서 가져온 store_id값과 일치하는)
        store = get_object_or_404(rsv.Store, pk=requested_store_id)

        if store:
            context['store'] = store

            # Store의 owner(User 객체)와 연결된 Manager 찾기
            manager_of_the_store = Manager.objects.filter(user=store.owner).first()
            # print("찍어보자2", manager_of_the_store)
            
            if manager_of_the_store:
                context['manager'] = manager_of_the_store

            # Store의 pk값과 Store_times의 store_id값과 일치하는 Store_times 가져오기
            sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk)
            context['sto_time_objects'] = sto_time_objects
            # print("찍어보자3", sto_time_objects)
            # print("찍어보자3-1", sto_time_objects.values)
            
            
            sto_time_values_list  = {
                'store_id': store.pk,
                'sto_time': list(sto_time_objects.values()),
            }

            print()
            # print("찍어보자4 ", sto_time_values_list)
            print()


            # 예약 정보 가져오기
            # Reservation_user
            disabled_dates_info_list = []
            for sto_time in sto_time_objects:
                reservation_user_objects = rsv.Reservation_user.objects.filter(
                    Q(store_id=store) &
                    Q(user_time=sto_time.reservation_time)
                )

                # Reservation_user(사용자 예약내역)가 존재하면: 
                # hour_disabled_dates_dict에 추가
                if reservation_user_objects.exists():  # Add this line
                    hour_disabled_dates_dict = {}

                    for reservation in reservation_user_objects:
                        user_date_str = reservation.reservation_date
                        # print("user_date_str찍어보기", user_date_str)
                                
                        datetime_obj = datetime.strptime(reservation.user_time, '%H:%M')
                        
                        # print("datetime_obj찍어보기", datetime_obj)
                        formatted_time_str = datetime_obj.strftime('%H:%M')
                        # print("formatted_time_str찍어보기", formatted_time_str)

                        if user_date_str not in hour_disabled_dates_dict:
                            hour_disabled_dates_dict[user_date_str] = []

                        hour_disabled_dates_dict[user_date_str].append(formatted_time_str)

                    disabled_dates_info_list.append({
                        'hour_disabled_dates': hour_disabled_dates_dict,
                        'user_date': [info.reservation_date for info in reservation_user_objects],
                        'disable_time': [datetime.strptime(info.user_time, '%H:%M').strftime("%H:%M") for info in reservation_user_objects]
                    })
                    
            # 예약이 불가능한 날짜와 시간을 가져와 disabled_dates_info_json에 저장
            context['disabled_dates_info_json'] = json.dumps(disabled_dates_info_list , cls=DjangoJSONEncoder)
        # print(context['disabled_dates_info_json'])

        # print("콘텍스트", context)
        return context




    # update함수 만들기
    def post(self, request, *args, **kwargs):

        # context = super(Update, self).get_context_data(**kwargs)
        

        # URL에서 store_id값 가져오기
        requested_store_id = self.kwargs.get('store_id')

        # Store테이블의 id값을 가진 객체찾기 (url에서 가져온 store_id값과 일치하는)
        store = get_object_or_404(rsv.Store, pk=requested_store_id)

        if store:
            # Store의 owner(User 객체)와 연결된 Manager 찾기
            manager_of_the_store = Manager.objects.filter(user=store.owner).first()


            # Store의 pk값과 Store_times의 store_id값과 일치하는 Store_times 가져오기
            sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk)
            # print("sto_time_objects", sto_time_objects)
            # print("sto_time_objects갯수", len(sto_time_objects))
            # print()

            # HttpResponseRedirect를 위한 전달인자
            pk_value = manager_of_the_store.pk
            store_id_value = requested_store_id
            

            # sto_time_objects의 reservation_time 값들을 리스트로 가져오기
            original_time = list(sto_time_objects.values_list('reservation_time', flat=True))
            print("original_time", original_time)
            print()


            # post요청
            if request.method == 'POST':
                button_values_str = request.POST.get('button_values')
                added_time = json.loads(button_values_str)
                print()
                print("button_values_str찍기", button_values_str)
                print("added_time찍기", added_time)
                print()


                # Reservation_user에서 예약 정보 가져오기
                reserved_time = []
                for sto_time in sto_time_objects:
                    reservation_user_objects = rsv.Reservation_user.objects.filter(
                        Q(store_id=store) &
                        Q(user_time=sto_time.reservation_time)
                    )

                    # 사용자 예약내역이 존재하면:
                    if reservation_user_objects.exists():
                        for reservation in reservation_user_objects:

                            # user_date_str = reservation.reservation_date
                            # print("user_date_str찍어보기", user_date_str)
                            datetime_obj = datetime.strptime(reservation.user_time, '%H:%M')
                            print("datetime_obj찍어보기", datetime_obj)
                            formatted_time_str = datetime_obj.strftime('%H:%M')
                            print("formatted_time_str찍어보기", formatted_time_str)
                            print("="*30)

                            reserved_time.append(formatted_time_str)

                        
                print("예약된시간", reserved_time)
                print("예약된시간갯수", len(reserved_time))
                

                # original_time : 사장님이 저장했던 기존시간값
                # reserved_time : 사용자 예약이 존재하는 시간
                # added_time : 사장님이 변경할 시간 (프론트에서 요청이 들어온)


                original_time_set = set(original_time)
                print("original_time_set", original_time_set)
                added_time_set = set(added_time)
                # 교집합
                matching_times_set = original_time_set & added_time_set
                check_added_set = added_time_set - original_time_set

                print("matching_times_set", matching_times_set)
                print("matching_times_set갯수", len(matching_times_set))
                print("check_added_set갯수", len(check_added_set))
                print("="*30)
                print()

                # if all_time_in_added_time:
                # 모든 시간이 일치하는 경우
                if matching_times_set == original_time_set:
                    print("CASE1/ 모든 시간이 존재")
                    for time in added_time:
                        sto_time, created = rsv.Store_times.objects.get_or_create(
                            store_id=store,
                            reservation_time=time,
                        )
                        if created:
                            print(f"{time}에 대한 새로운 Store_times 객체가 생성되었습니다.")

                # 일부 시간이 일치하는 경우
                elif len(matching_times_set) > 0:
                    print("CASE2/ 일부 시간이 존재")
                    # 삭제된 시간은 삭제
                    for time in original_time_set - matching_times_set:
                        rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                        # rsv.Store_times.save()
                        print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

                    # 추가된 시간은 추가
                    for time in added_time_set - matching_times_set:
                        new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
                        # rsv.Store_times.save()
                        new_store_time.save()
                        print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

                # 시간이 하나도 일치하지 않는 경우
                elif len(matching_times_set) == 0:
                    print("CASE3/ 시간이 하나도 일치X")
                    print("added_time_set갯수", len(added_time_set))
                    print("original_time_set갯수", len(original_time_set))

                    # 기존 시간값이 모두 없을경우(삭제 혹은 변경)
                    # 이건 삭제를 프론트에서 아직 처리안해줬기때문에 프론트 수정후 테스트가능
                    if len(original_time_set) == 0:
                        print("3-1/ 기존 시간값이 모두 삭제된경우")

                        # original_time 삭제
                        for time in original_time_set:
                            rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                            print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

                        for time in added_time_set:
                            new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
                            new_store_time.save()
                            print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

                    # # 기존 시간값이 모두 변경(삭제후 추가)된 경우
                    # elif len(added_time_set) != 0 and len(original_time_set) != 0 and len(added_time_set) == len(original_time_set):
                    #     print("3-2/ 기존 시간값이 모두 변경된경우")

                    #     # original_time 삭제, added_time 추가
                    #     for time in original_time_set:
                    #         rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                    #         print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

                    #     for time in added_time_set:
                    #         new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
                    #         new_store_time.save()
                    #         print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")
                        
                    # 그 외
                    elif len(check_added_set) == len(added_time_set):
                        # 추가된 시간 - 기존시간을 뺀 값 갯수 = 추가된 시간 갯수 일경우:
                        # 오리지널이 없거나 변경되는 경우도 추가해줘야함..
                        # 애초에 기준값을 오리지널로 잡았기때문에 자꾸 else에 걸리는거
                        # 오류잡기용
                        print("3-3/ 추가된시간값과 기존시간값의 갯수가 다르거나 값이 존재")
                        for time in original_time_set:
                            rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                            print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")
                        
                        for time in added_time_set:
                            new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
                            new_store_time.save()
                            print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

                    else: 
                        print("3-4/ 그외")




                    # # 기존 시간값이 모두 삭제된경우
                    # # 이건 삭제를 프론트에서 아직 처리안해줬기때문에 프론트 수정후 테스트가능
                    # if len(added_time_set) == 0 and len(original_time_set) == 0:
                    #     print("3-1/ 기존 시간값이 모두 삭제된경우")

                    #     # original_time 삭제
                    #     for time in original_time_set:
                    #         rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                    #         print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

                    # # 기존 시간값이 모두 변경(삭제후 추가)된 경우
                    # elif len(added_time_set) != 0 and len(original_time_set) != 0 and len(added_time_set) == len(original_time_set):
                    #     print("3-2/ 기존 시간값이 모두 변경된경우")

                    #     # original_time 삭제, added_time 추가
                    #     for time in original_time_set:
                    #         rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
                    #         print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

                    #     for time in added_time_set:
                    #         new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
                    #         new_store_time.save()
                    #         print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")
                        
                    # # 그 외
                    # else:
                    #     # 오리지널이 없거나 변경되는 경우도 추가해줘야함..
                    #     # 애초에 기준값을 오리지널로 잡았기때문에 자꾸 else에 걸리는거
                    #     # 오류잡기용
                    #     print("3-3/ 추가된시간값과 기존시간값의 갯수가 다르거나 값이 존재")
                    #     for time in added_time:
                    #         sto_time, created = rsv.Store_times.objects.get_or_create(
                    #             store_id=store,
                    #             reservation_time=time,
                    #         )
                    #         if created:
                    #             print(f"{time}에 대한 새로운 Store_times 객체가 생성되었습니다.")

                # POST 처리 완료 시 리디렉션
                return HttpResponseRedirect(reverse('update', kwargs={'pk': pk_value, 'store_id': store_id_value}))
        
        return self.get(request, *args, **kwargs)
    



    
