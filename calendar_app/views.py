
import bcrypt

from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView, View
from calendar_app import models

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
import json
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib import messages
from datetime import datetime, timedelta
from django.forms.models import model_to_dict

# 이름변경
class First_list(ListView):
    model = models.Store
    template_name = "calendar_app/main1.html"

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
    
    return render(request, 'calendar_app/write.html')

# from django.shortcuts import render

# # Create your views here.

# def list_up(request):
#     return render(request, "main1.html")

def reserve(request):
    return render(request, "calendar_app/main2.html")

# def info(request):
#     return render(request, "main3.html")

class Test_list(TemplateView):
    template_name = "calendar_app/main4_sungwoo.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_list = models.Store.objects.all()
        context['store_list'] = store_list

        store_times_dict = {}
        for store in store_list:
            store_times = models.Store_times.objects.filter(store_id=store.pk)
            store_times_dict[store.pk] = store_times
        context['store_times_dict'] = store_times_dict

        pk = self.kwargs.get('pk')
        if pk:
            store = get_object_or_404(models.Store, pk=pk)
        else:
            store = None

        if store:
            store_list = [store]
        else:
            store_list = store_list
        
        store_data = []
        
        for store in store_list:
            sto_time = models.Store_times.objects.filter(store_id=store.pk)
            print(store)
            store_dates = []
            for dates in sto_time:
                dates_info  = models.Reservation_user.objects.filter(
                Q(store_id=store) &
                Q(user_time=dates.reservation_time) 
                )
                

                hour_disabled_dates = {}

                for res in dates_info:
                    user_date = res.reservation_date
                    user_time = res.user_time

                    # 일부 예약이 이미 비활성 시간에 추가된 경우 해당 시간을 추가하고, 그렇지 않은 경우 새로운 항목을 만듭니다.
                    if user_date in hour_disabled_dates:
                        hour_disabled_dates[user_date].append(user_time)
                    else:
                        hour_disabled_dates[user_date] = [user_time]

                store_dates.append({
                    'hour_disabled_dates': hour_disabled_dates, # current_hour_reservations를 제거
                })

                
                user_dates = [info.reservation_date for info in dates_info]
                store_dates.append({
                'user_date': user_dates,
                'disable_time': json.dumps([info.user_time for info in dates_info ])
                })
                # print(store_dates)
            store_data.append({
                'store_id': store.pk,
                'sto_time': list(sto_time.values()),
                'store_dates_json': json.dumps(store_dates, cls=DjangoJSONEncoder),
            })

        # context['store_data'] = store_data
        context['store_data_json'] = json.dumps(store_data, cls=DjangoJSONEncoder)
        # print(store_data)
        return context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            store_id = request.POST["selected_store2"]
            sto = get_object_or_404(models.Store, pk=store_id)

            rst_user = models.Reservation_user()
            rst_user.user_name = request.POST["detail_user_name"]
            rst_user.user_phone = request.POST["detail_user_phone"]
            rst_user.reservation_date = request.POST["detail_user_date"]
            rst_user.user_time = request.POST["detail_user_time"]
            rst_user.store_id = sto
            rst_user.save()

            # POST 처리 완료 시 리디렉션
            return HttpResponseRedirect(reverse('Test_list'))

        return self.get(request, *args, **kwargs)


# 메인
class Idx_list(TemplateView):
    template_name = "calendar_app/main.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store_list = models.Store.objects.all()
        context['store_list'] = store_list

        store_times_dict = {}
        for store in store_list:
            store_times = models.Store_times.objects.filter(store_id=store.pk)
            store_times_dict[store.pk] = store_times
        context['store_times_dict'] = store_times_dict

        pk = self.kwargs.get('pk')
        if pk:
            store = get_object_or_404(models.Store, pk=pk)
        else:
            store = None

        if store:
            store_list = [store]
        else:
            store_list = store_list
        
        store_data = []
        
        for store in store_list:
            sto_time = models.Store_times.objects.filter(store_id=store.pk)
            print(store)
            store_dates = []
            for dates in sto_time:
                dates_info  = models.Reservation_user.objects.filter(
                Q(store_id=store) &
                Q(user_time=dates.reservation_time) 
                )
                

                hour_disabled_dates = {}

                for res in dates_info:
                    user_date = res.reservation_date
                    user_time = res.user_time

                    # 일부 예약이 이미 비활성 시간에 추가된 경우 해당 시간을 추가하고, 그렇지 않은 경우 새로운 항목 생성
                    if user_date in hour_disabled_dates:
                        hour_disabled_dates[user_date].append(user_time)
                    else:
                        hour_disabled_dates[user_date] = [user_time]

                store_dates.append({
                    'hour_disabled_dates': hour_disabled_dates, # current_hour_reservations를 제거
                })

                
                user_dates = [info.reservation_date for info in dates_info]
                store_dates.append({
                'user_date': user_dates,
                'disable_time': json.dumps([info.user_time for info in dates_info ])
                })
                # print(store_dates)
            store_data.append({
                'store_id': store.pk,
                'sto_time': list(sto_time.values()),
                'store_dates_json': json.dumps(store_dates, cls=DjangoJSONEncoder),
            })

        # context['store_data'] = store_data
        context['store_data_json'] = json.dumps(store_data, cls=DjangoJSONEncoder)
        # print(store_data)
        return context
    
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            store_id = request.POST["selected_store2"]
            sto = get_object_or_404(models.Store, pk=store_id)

            rst_user = models.Reservation_user()
            rst_user.user_name = request.POST["detail_user_name"]
            rst_user.user_phone = request.POST["detail_user_phone"]
            rst_user.reservation_date = request.POST["detail_user_date"]
            rst_user.user_time = request.POST["detail_user_time"]
            rst_user.visitor_num = int(request.POST["v_num"])
            rst_user.store_id = sto

            # 그냥 입력받은 password
            password = request.POST["password"]


            # 암호화
            salt = bcrypt.gensalt()
            to_byte_pw = password.encode('utf-8')
            salted_pw = bcrypt.hashpw(to_byte_pw, salt)
            to_str_pw = salted_pw.decode('utf-8')
            rst_user.pwhash = to_str_pw


            try:
                rst_user.full_clean()  # 모델의 유효성 검사 수행
                rst_user.save()
            except ValidationError as e:
                # 유효성 검사 실패 시 에러
                error_message = str(e)
                return HttpResponse(error_message, status=400)

            # POST 처리 완료 시 리디렉션
            return HttpResponseRedirect(reverse('Idx_list'))

        return self.get(request, *args, **kwargs)


# 예약확인
class FindReservationView(View):
    template_name = 'calendar_app/find_reservation.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        user_name = request.POST.get('user_name').strip()
        user_phone = request.POST.get('user_phone')

        try:
            reservation = models.Reservation_user.objects.get(user_name=user_name, user_phone=user_phone)
        except models.Reservation_user.DoesNotExist:
            messages.error(request, "해당하는 예약 정보가 없습니다.")
            return render(request, self.template_name, {'anchor1': 'anchor1'})

        request.session['reservation'] = model_to_dict(reservation)  # model_to_dict: dict로 변환

        url = reverse('input_user_pw')
        # url = reverse('input_user_pw') + '#anchor2'
        return HttpResponseRedirect(url)
    

# # 본인확인(수정전)
# class InputUserNameView(View):
#     def get(self, request):
#         return render(request, 'calendar_app/input_user_pw.html')


#     def post(self, request):
#             input_pw = request.POST.get('input_pw')
#             reservation = request.session.get('reservation')


#             # DB에 저장된 암호화된 비밀번호
#             hashed_pw = reservation.get('pwhash')

#             if input_pw and hashed_pw:
#                 input_pw = input_pw.encode('utf-8')
#                 hashed_pw = hashed_pw.encode('utf-8')

#                 check_pw = bcrypt.checkpw(input_pw, hashed_pw)
#                 print("확인", check_pw)

#                 if check_pw:
#                     request.session['pw_checked'] = True
#                 else:
#                     request.session['pw_checked'] = False
#             else:
#                 request.session['pw_checked'] = False
            
#             # 이동할 url
#             url = reverse('detail_view')
#             # url = reverse('detail_view') + '#anchor3'
#             return HttpResponseRedirect(url)
    

# # 본인확인(수정1)
# class InputUserNameView(View):

#     MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

#     # 남은시간 계산
#     def calculate_remaining_time(self, last_login_date, now):
#         remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
#         return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds
    
#     def get(self, request):
#         now = datetime.now()
#         reservation = request.session.get('reservation')
#         context = {}
        

#         try:
#             pw_checked = request.session.get('pw_checked')
#             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#             # 추가
#             # context['reservation'] = reservations
#         except models.Reservation_user.DoesNotExist:
#             context['warning'] = "예약 정보가 존재하지 않습니다."
#             print("콘텍스트 출력1 ", context)
#             return render(request, 'calendar_app/input_user_pw.html', context)
#             # return JsonResponse(context, safe=False)

#         login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        

#         if pw_checked == False:

#             context['warning'] = "비밀번호 확인이 필요합니다."
            
#             if login_infos.is_block == 'Y':
#                 # 남은시간표시
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     # 'warning': None,
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                     'has_waiting_time': None,
#                 }
                
#                 if now - login_infos.last_login_date < timedelta(minutes=1):
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
#                         print("콘텍스트 출력2 ", context)
#                     else:
#                         context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
#                         print("콘텍스트 출력3 ", context)
#                 elif login_infos.block_count < self.MAX_BLOCK_COUNT:
#                     login_infos.retry_login = 5
#                     login_infos.is_block = 'N'
#                     login_infos.block_count += 1
#                     login_infos.save()
#                 else:
#                     context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                     context['has_waiting_time'] = False
#                     print("콘텍스트 출력4 ", context)
            
#             else:
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)
#                 login_infos.retry_login -= 1
#                 login_infos.last_login_date = datetime.now()
#                 if login_infos.retry_login == 0:
#                     login_infos.is_block = 'Y'
#                     login_infos.save()
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                             'has_waiting_time': True,
#                         }
#                         print("콘텍스트 출력6 ", context)
#                     else:
#                         login_infos.block_count += 1
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                         }
#                         print("콘텍스트 출력7 ", context)
                                
#                 login_infos.save()
#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     'warning': "비밀번호가 일치하지 않습니다.",
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                 }
#                 print("콘텍스트 출력8 ", context)

#         elif pw_checked:
#                 login_infos.retry_login = 5
#                 login_infos.is_block = 'N'
#                 login_infos.save()
#                 context = {'reservation': reservations}
#                 print("콘텍스트 출력5 ", context)
        
#         # return JsonResponse(context, safe=False)
#         return render(request, 'calendar_app/input_user_pw.html', context)


#     def post(self, request):
#             if 'form1' in request.POST:
#                 context = {}
#                 input_pw = request.POST.get('input_pw')
#                 reservation = request.session.get('reservation')


#                 # DB에 저장된 암호화된 비밀번호
#                 hashed_pw = reservation.get('pwhash')

#                 if input_pw and hashed_pw:
#                     input_pw = input_pw.encode('utf-8')
#                     hashed_pw = hashed_pw.encode('utf-8')

#                     check_pw = bcrypt.checkpw(input_pw, hashed_pw)
#                     print("확인", check_pw)

#                     if check_pw:
#                         request.session['pw_checked'] = True
#                     else:
#                         request.session['pw_checked'] = False
#                 else:
#                     request.session['pw_checked'] = False
                
#                 # # 이동할 url
#                 # url = reverse('detail_view')
#                 # # url = reverse('detail_view') + '#anchor3'
#                 # return HttpResponseRedirect(url)
#                 context['form_submitted'] = True
#                 return render(request, 'calendar_app/input_user_pw.html', context)
#                 # return render(request, 'calendar_app/input_user_pw.html')
            
#             elif 'form2' in request.POST:
#                 reservation = request.session.get('reservation')
#                 pw_checked = request.session.get('pw_checked')
#                 # input_user_pw = request.session.get('input_user_pw')

#                 try:
#                     # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
#                     if pw_checked:
#                         reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#                 except models.Reservation_user.DoesNotExist:
#                     return render(request, 'calendar_app/input_user_pw.html', {'invalid_access': True})
                
#                 reservations.delete()  # 조회한 예약삭제
#                 url = reverse('reservation_deleted_view')
#                 # url = reverse('reservation_deleted_view') + '#anchor4'
#                 return HttpResponseRedirect(url)
#                 # return JsonResponse(context, safe=False)
    


# 여기에 빈 딕셔너리 만들고
    

# 공통코드 빼기
class CommonLogicMixin:
    MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

    # 남은시간 계산
    def calculate_remaining_time(self, last_login_date, now):
        remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
        return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds
    
    def common_logic(self, request):
        now = datetime.now()
        reservation = request.session.get('reservation')
        context = {}
        
        try:
            pw_checked = request.session.get('pw_checked')
            reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
            # 추가
            # context['reservation'] = reservations
            # data = [model_to_dict(reserve1) for reserve1 in Store_times]
        except models.Reservation_user.DoesNotExist:
            context['warning'] = "예약 정보가 존재하지 않습니다."
            print("콘텍스트 출력1 ", context)
            return context, None
            # return JsonResponse(context, safe=False)

        login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        # test하는중
        # Store_times = models.Store_times.objects.all()
        # data = [model_to_dict(reserve1) for reserve1 in Store_times]

        if pw_checked == False:

            context['warning'] = "비밀번호 확인이 필요합니다."
            
            if login_infos.is_block == 'Y':
                # 남은시간표시
                remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

                context = {
                    'remaining_time_in_seconds': remaining_time_in_seconds,
                    # 'warning': None,
                    'retry_login': login_infos.retry_login,
                    'block_count': login_infos.block_count,
                    # 'has_waiting_time': False,
                    # 'reservation': reservations,
                    # 'Store_times' : data
                }
                
                if now - login_infos.last_login_date < timedelta(minutes=1):
                    if login_infos.block_count >= self.MAX_BLOCK_COUNT:
                        context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
                        context['has_waiting_time'] = False
                        print("콘텍스트 출력2 ", context)
                    else:
                        context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
                        context['has_waiting_time'] = True
                        print("콘텍스트 출력3 ", context)
                elif login_infos.block_count < self.MAX_BLOCK_COUNT:
                    login_infos.retry_login = 5
                    # 추가추가추가 - (5-1=4)부터 시작
                    login_infos.retry_login -= 1
                    login_infos.is_block = 'N'
                    # 얘없애도되나
                    # login_infos.block_count += 1
                    login_infos.save()
                    # 에러뜨는부분
                    # context['warning'] = "비밀번호가 일치하지 않습니다."
                    # context['has_waiting_time'] = False

                    
                    context = {
                        # 'remaining_time_in_seconds': remaining_time_in_seconds,
                        'warning': "비밀번호가 일치하지 않습니다.",
                        'retry_login': login_infos.retry_login,
                        'block_count': login_infos.block_count,
                        'has_waiting_time': False,
                    }
                    print("이거봐", context)

                else:
                    context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
                    context['has_waiting_time'] = False
                    print("콘텍스트 출력4 ", context)
            
            else:
                remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)
                print("몇개 ", login_infos.retry_login)
                if not created:  # login_infos를 첫 생성시에는 retry_login-1하지않음
                    login_infos.retry_login -= 1
                login_infos.last_login_date = datetime.now()
                if login_infos.retry_login == 0:
                    login_infos.is_block = 'Y'
                    login_infos.save()
                    if login_infos.block_count >= self.MAX_BLOCK_COUNT:
                        context = {
                            # has_waiting_time False 추가
                            'remaining_time_in_seconds': remaining_time_in_seconds,
                            'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
                            'retry_login': login_infos.retry_login,
                            'block_count': login_infos.block_count,
                            # 원래 T
                            'has_waiting_time': False,
                        }
                        print("콘텍스트 출력6 ", context)
                    else:
                        login_infos.block_count += 1
                        # 추가추가추가 01.27 3이아닐때만 context뜨게
                        if login_infos.block_count != self.MAX_BLOCK_COUNT:
                            context = {
                                # has_waiting_time True 추가
                                'remaining_time_in_seconds': remaining_time_in_seconds,
                                'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
                                'retry_login': login_infos.retry_login,
                                'block_count': login_infos.block_count,
                                'has_waiting_time': True,
                            }
                        else:
                            context = {
                                # 'remaining_time_in_seconds': remaining_time_in_seconds,
                                'warning': "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요.",
                                'retry_login': login_infos.retry_login,
                                'block_count': login_infos.block_count,
                                'has_waiting_time': False,
                            }
                        print("콘텍스트 출력7 ", context)
                                
                login_infos.save()
                if login_infos.retry_login != 0:
                    print("이거")
                    context = {
                        'remaining_time_in_seconds': remaining_time_in_seconds,
                        'warning': "비밀번호가 일치하지 않습니다.",
                        'retry_login': login_infos.retry_login,
                        'block_count': login_infos.block_count,
                        'has_waiting_time': False,
                    }
                    print("콘텍스트 출력8 ", context)

        elif pw_checked:
                login_infos.retry_login = 5
                login_infos.is_block = 'N'
                login_infos.save()
                context = {
                    'reservation': reservations,
                    # 'test': 'sksk',
                           }
                print("콘텍스트 출력5 ", context)


        # # context의 'reservation' 항목을 JSON 직렬화 가능한 형태로 변환
        # if 'reservation' in context:
        #     context['reservation'] = model_to_dict(context['reservation'])

        # context를 세션에 저장
        if 'warning' in context:
            request.session['context_return'] = context.get('warning')
        # yaya = context.get('warning')
        # print("타입찍기 ", type(yaya), yaya)
        # print("워닝만찍어보기 ", yaya)

        return context, login_infos



# 본인확인(수정2)
class InputUserNameView(CommonLogicMixin, View):

    # MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

    # # 남은시간 계산
    # def calculate_remaining_time(self, last_login_date, now):
    #     remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
    #     return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds
    
    def get(self, request):
        context, login_infos = self.common_logic(request)
        if login_infos is not None:
            login_infos.save()
        return render(request, 'calendar_app/input_user_pw.html', context)
        

    def post(self, request):
            if 'form1' in request.POST:
                context = {}
                input_pw = request.POST.get('input_pw')
                reservation = request.session.get('reservation')
                booking_lists = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])


                # DB에 저장된 암호화된 비밀번호
                hashed_pw = reservation.get('pwhash')

                if input_pw and hashed_pw:
                    input_pw = input_pw.encode('utf-8')
                    hashed_pw = hashed_pw.encode('utf-8')

                    check_pw = bcrypt.checkpw(input_pw, hashed_pw)
                    # context['form_submitted'] = True

                    print("확인", check_pw)

                    if check_pw:
                        request.session['pw_checked'] = True
                        context = {
                        'booking': booking_lists,
                        'pw_checked': request.session['pw_checked'],
                        # 'test': 'sksk',
                            }
                        # context = {
                        #     'warning': request.session.get('context_return'),
                        #     }
                    else:
                        request.session['pw_checked'] = False
                        context['pw_checked'] = request.session['pw_checked']
                        print("패스워드확인여부1 ", context)
                        # context['warning'] = request.session.get('context_return')
                        # print("얘도찍어봐 ", request.session.get('context_return'))
                        # print("콘텍스트 잘들어감1? ", context)
                        
                        # 잠시...
                        # submission = request.POST.get('submission', 'false') == 'true'
                        # if submission:
                        #     # 폼 제출 처리
                        #     # 비밀번호 확인, retryLogin 감소 등
                        # else:
                        #     # 폼 제출이 아닌 경우 (새로 고침 등)
                else:
                    request.session['pw_checked'] = False
                    context['pw_checked'] = request.session['pw_checked']
                    print("패스워드확인여부2 ", context)
                    # context['warning'] = request.session.get('context_return')
                    # print("콘텍스트 잘들어감2? ", context)
                    # context['form_submitted'] = False
                
                # # 이동할 url
                # url = reverse('detail_view')
                # # url = reverse('detail_view') + '#anchor3'
                # return HttpResponseRedirect(url)
                context['form_submitted'] = True
                # 추가함....
                context['pw_checked'] = request.session['pw_checked']
                # test하는중2
                # context['test'] = 'meme'

                return render(request, 'calendar_app/input_user_pw.html', context)
                # return render(request, 'calendar_app/input_user_pw.html')
            
            elif 'form2' in request.POST:
                reservation = request.session.get('reservation')
                pw_checked = request.session.get('pw_checked')
                # input_user_pw = request.session.get('input_user_pw')

                try:
                    # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
                    if pw_checked:
                        reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
                except models.Reservation_user.DoesNotExist:
                    return render(request, 'calendar_app/input_user_pw.html', {'invalid_access': True})
                
                reservations.delete()  # 조회한 예약삭제
                url = reverse('reservation_deleted_view')
                # url = reverse('reservation_deleted_view') + '#anchor4'
                return HttpResponseRedirect(url)
                # return JsonResponse(context, safe=False)


# ## 예약 조회 및 취소 (수정) -detailview 삭제
# class DetailView(View):
#     template_name = 'calendar_app/reservation_detail.html'
#     MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

#     # 남은시간 계산
#     def calculate_remaining_time(self, last_login_date, now):
#         remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
#         return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds

#     # def calculate_remaining_time(self, last_login_date, now):
#     #     return 600 - int((now - last_login_date).total_seconds())


#     def get(self, request):
#         now = datetime.now()
#         reservation = request.session.get('reservation')
#         context = {}
        

#         try:
#             pw_checked = request.session.get('pw_checked')
#             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#         except models.Reservation_user.DoesNotExist:
#             context['warning'] = "예약 정보가 존재하지 않습니다."
#             print("콘텍스트 출력1 ", context)
#             return render(request, self.template_name, context)

#         login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        

#         if pw_checked == False:

#             context['warning'] = "비밀번호 확인이 필요합니다."
            
#             # 정지여부(is_block), 정지횟수(block_count) 확인
#             if login_infos.is_block == 'Y':
#                 # 남은시간표시
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     # 'warning': None,
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                     'has_waiting_time': None,
#                 }


#                 # 위치 수정하기....
#                 # 세션에서 비밀번호 확인 여부를 확인
                
#                 if now - login_infos.last_login_date < timedelta(minutes=1):
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
#                         print("콘텍스트 출력2 ", context)
#                     else:
#                         context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
#                         print("콘텍스트 출력3 ", context)
#                 elif login_infos.block_count < self.MAX_BLOCK_COUNT:
#                     login_infos.retry_login = 5
#                     login_infos.is_block = 'N'
#                     login_infos.block_count += 1
#                     login_infos.save()
#                 else:
#                     context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                     context['has_waiting_time'] = False
#                     print("콘텍스트 출력4 ", context)
            
#             else:
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)
#                 login_infos.retry_login -= 1
#                 login_infos.last_login_date = datetime.now()
#                 if login_infos.retry_login == 0:
#                     login_infos.is_block = 'Y'
#                     login_infos.save()
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                             'has_waiting_time': True,
#                         }
#                         print("콘텍스트 출력6 ", context)
#                     else:
#                         login_infos.block_count += 1
#                         # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요."
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                             # 'has_waiting_time': True
#                         }
#                         print("콘텍스트 출력7 ", context)
                                
#                 login_infos.save()
#                 # context['warning'] = "비밀번호가 일치하지 않습니다."
#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     'warning': "비밀번호가 일치하지 않습니다.",
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                 }
#                 print("콘텍스트 출력8 ", context)

#         elif pw_checked:
#                 login_infos.retry_login = 5
#                 login_infos.is_block = 'N'
#                 login_infos.save()
#                 context = {'reservation': reservations}
#                 print("콘텍스트 출력5 ", context)
        


#         return render(request, self.template_name, context)


#     def post(self, request):
#         reservation = request.session.get('reservation')
#         pw_checked = request.session.get('pw_checked')
#         # input_user_pw = request.session.get('input_user_pw')

#         try:
#             # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
#             if pw_checked:
#                 reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#         except models.Reservation_user.DoesNotExist:
#             return render(request, self.template_name, {'invalid_access': True})
        
#         reservations.delete()  # 조회한 예약삭제
#         url = reverse('reservation_deleted_view')
#         # url = reverse('reservation_deleted_view') + '#anchor4'
#         return HttpResponseRedirect(url)




# 취소후 화면
class ReservationDeletedView(View):
    template_name = 'calendar_app/reservation_deleted.html'

    def get(self, request):
        return render(request, self.template_name)
    


# class FetchView(View):
#     # template_name = 'calendar_app/reservation_detail.html'

#     def get(self, request):
#         # context = {
#         #     "test": True,
#         # }
#         context = {
#                             # 'remaining_time_in_seconds': 5,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
#                             'retry_login': 5,
#                             'block_count': 5,
#                             'has_waiting_time': True,
#                         }
#         # return render (request, context)
#         # return JsonResponse([], safe=False)
#         # return JsonResponse({'has_waiting_time': True}, safe=False)
#         return JsonResponse(context, safe=False)



# # 수정전
# class FetchView(View):
#     # template_name = 'calendar_app/reservation_detail.html'
#     MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

#     # 남은시간 계산
#     def calculate_remaining_time(self, last_login_date, now):
#         remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
#         return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds

#     def get(self, request):
#         now = datetime.now()
#         reservation = request.session.get('reservation')
#         context = {}
        

#         try:
#             pw_checked = request.session.get('pw_checked')
#             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#         except models.Reservation_user.DoesNotExist:
#             context['warning'] = "예약 정보가 존재하지 않습니다."
#             print("콘텍스트 출력1 ", context)
#             # return render(request, self.template_name, context)
#             return JsonResponse(context, safe=False)

#         login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        

#         if pw_checked == False:

#             context['warning'] = "비밀번호 확인이 필요합니다."
            
#             # 정지여부(is_block), 정지횟수(block_count) 확인
#             if login_infos.is_block == 'Y':
#                 # 남은시간표시
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     # 'warning': None,
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                     'has_waiting_time': None,
#                 }


#                 # 위치 수정하기....
#                 # 세션에서 비밀번호 확인 여부를 확인
                
#                 if now - login_infos.last_login_date < timedelta(minutes=1):
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
#                         print("콘텍스트 출력2 ", context)
#                     else:
#                         context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
#                         print("콘텍스트 출력3 ", context)
#                 elif login_infos.block_count < self.MAX_BLOCK_COUNT:
#                     login_infos.retry_login = 5
#                     login_infos.is_block = 'N'
#                     login_infos.block_count += 1
#                     login_infos.save()
#                 else:
#                     context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                     context['has_waiting_time'] = False
#                     print("콘텍스트 출력4 ", context)
            
#             else:
#                 remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)
#                 login_infos.retry_login -= 1
#                 login_infos.last_login_date = datetime.now()
#                 if login_infos.retry_login == 0:
#                     login_infos.is_block = 'Y'
#                     login_infos.save()
#                     if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                         # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                             'has_waiting_time': True,
#                         }
#                         print("콘텍스트 출력6 ", context)
#                     else:
#                         login_infos.block_count += 1
#                         # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요."
#                         context = {
#                             'remaining_time_in_seconds': remaining_time_in_seconds,
#                             'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
#                             'retry_login': login_infos.retry_login,
#                             'block_count': login_infos.block_count,
#                             # 'has_waiting_time': True
#                         }
#                         print("콘텍스트 출력7 ", context)
                                
#                 login_infos.save()
#                 # context['warning'] = "비밀번호가 일치하지 않습니다."
#                 context = {
#                     'remaining_time_in_seconds': remaining_time_in_seconds,
#                     'warning': "비밀번호가 일치하지 않습니다.",
#                     'retry_login': login_infos.retry_login,
#                     'block_count': login_infos.block_count,
#                 }
#                 print("콘텍스트 출력8 ", context)

#         elif pw_checked:
#                 login_infos.retry_login = 5
#                 login_infos.is_block = 'N'
#                 login_infos.save()
#                 context = {'reservation': reservations}
#                 print("콘텍스트 출력5 ", context)
        


#         # return render(request, self.template_name, context)
#         return JsonResponse(context, safe=False)


#     # def post(self, request):
#     #     reservation = request.session.get('reservation')
#     #     pw_checked = request.session.get('pw_checked')
#     #     # input_user_pw = request.session.get('input_user_pw')

#     #     try:
#     #         # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
#     #         if pw_checked:
#     #             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#     #     except models.Reservation_user.DoesNotExist:
#     #         return render(request, 'calendar_app/input_user_pw.html', {'invalid_access': True})
        
#     #     reservations.delete()  # 조회한 예약삭제
#     #     url = reverse('reservation_deleted_view')
#     #     # url = reverse('reservation_deleted_view') + '#anchor4'
#     #     return HttpResponseRedirect(url)
#     #     # return JsonResponse(context, safe=False)



# 수정1
class FetchView(CommonLogicMixin, View):
    # template_name = 'calendar_app/reservation_detail.html'
    # MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

    # # 남은시간 계산
    # def calculate_remaining_time(self, last_login_date, now):
    #     remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
    #     return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds

    def get(self, request):
        context, _ = self.common_logic(request)
        print("찍어라 ", context)
        # return JsonResponse(context)
        
        if 'warning' in context:
            print("찍어라2 ", context)
            return JsonResponse(context,safe=False)
        else:
            print("찍어라3 ", context)
            # return HttpResponse()  # 빈 응답 반환
            return JsonResponse([],safe=False)  # 빈 응답 반환
        


    # def post(self, request):
    #     reservation = request.session.get('reservation')
    #     pw_checked = request.session.get('pw_checked')
    #     # input_user_pw = request.session.get('input_user_pw')

    #     try:
    #         # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
    #         if pw_checked:
    #             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
    #     except models.Reservation_user.DoesNotExist:
    #         return render(request, 'calendar_app/input_user_pw.html', {'invalid_access': True})
        
    #     reservations.delete()  # 조회한 예약삭제
    #     url = reverse('reservation_deleted_view')
    #     # url = reverse('reservation_deleted_view') + '#anchor4'
    #     return HttpResponseRedirect(url)
    #     # return JsonResponse(context, safe=False)