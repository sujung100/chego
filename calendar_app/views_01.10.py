
import bcrypt

from django.shortcuts import render, redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView, View
from calendar_app import models

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
import json
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.forms.models import model_to_dict
from django.contrib import messages
from datetime import datetime, timedelta


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

        url = reverse('input_user_pw') + '#anchor2'
        return HttpResponseRedirect(url)
    

# 본인확인
class InputUserNameView(View):
    def get(self, request):
        return render(request, 'calendar_app/input_user_pw.html')


    def post(self, request):
            input_pw = request.POST.get('input_pw')
            reservation = request.session.get('reservation')


            # DB에 저장된 암호화된 비밀번호
            hashed_pw = reservation.get('pwhash')

            if input_pw and hashed_pw:
                input_pw = input_pw.encode('utf-8')
                hashed_pw = hashed_pw.encode('utf-8')

                check_pw = bcrypt.checkpw(input_pw, hashed_pw)
                print("확인", check_pw)

                if check_pw:
                    # messages.error(request, "확인확인")
                    request.session['pw_checked'] = True
                    # url = reverse('detail_view') + '#anchor3'
                    # return HttpResponseRedirect(url)
                else:
                    # messages.error(request, "비밀번호가 일치하지 않습니다.")
                    request.session['pw_checked'] = False
                    # url = reverse('find_reservation') + '#anchor1'
                    # return HttpResponseRedirect(url)
                    # return render(request, 'calendar_app/input_user_pw.html')
            else:
                # 둘 중 하나가 없을 때,,근데 input속성으로 안넣으면 어짜피 submit불가
                # messages.error(request, "비밀번호가 입력되지 않았습니다.")
                request.session['pw_checked'] = False
                # url = reverse('find_reservation') + '#anchor1'
                # return HttpResponseRedirect(url)
                # return render(request, 'calendar_app/input_user_pw.html')
            
            # 이동할 url
            url = reverse('detail_view') + '#anchor3'
            return HttpResponseRedirect(url)


## 예약 조회 및 취소 (수정)
class DetailView(View):
    template_name = 'calendar_app/reservation_detail.html'
    MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

    # 남은시간 계산
    def calculate_remaining_time(self, last_login_date, now):
        remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
        return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds

    # def calculate_remaining_time(self, last_login_date, now):
    #     return 600 - int((now - last_login_date).total_seconds())


    def get(self, request):
        now = datetime.now()
        reservation = request.session.get('reservation')
        context = {}
        

        try:
            pw_checked = request.session.get('pw_checked')
            reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
        except models.Reservation_user.DoesNotExist:
            context['warning'] = "예약 정보가 존재하지 않습니다."
            print("콘텍스트 출력1 ", context)
            return render(request, self.template_name, context)

        login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        

        if pw_checked == False:
        # if not request.session.get('pw_checked', False):
            
        #     if 'form_submitted' in request.session:
        #         request.session['form_submitted'] = not request.session['form_submitted']
        #     else:
        #         request.session['form_submitted'] = False


            context['warning'] = "비밀번호 확인이 필요합니다."
            
            # 정지여부(is_block), 정지횟수(block_count) 확인
            if login_infos.is_block == 'Y':
                # 남은시간표시
                remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

                context = {
                    'remaining_time_in_seconds': remaining_time_in_seconds,
                    # 'warning': None,
                    'retry_login': login_infos.retry_login,
                    'block_count': login_infos.block_count,
                    'has_waiting_time': None,
                }


                # 위치 수정하기....
                # 세션에서 비밀번호 확인 여부를 확인
                
                if now - login_infos.last_login_date < timedelta(minutes=1):
                    if login_infos.block_count >= self.MAX_BLOCK_COUNT:
                        context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
                        print("콘텍스트 출력2 ", context)
                    else:
                        context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
                        print("콘텍스트 출력3 ", context)
                elif login_infos.block_count < self.MAX_BLOCK_COUNT:
                    login_infos.retry_login = 5
                    login_infos.is_block = 'N'
                    login_infos.block_count += 1
                    login_infos.save()
                else:
                    context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
                    context['has_waiting_time'] = False
                    print("콘텍스트 출력4 ", context)
            
            else:
                remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)
                login_infos.retry_login -= 1
                login_infos.last_login_date = datetime.now()
                # context = {
                #     'remaining_time_in_seconds': remaining_time_in_seconds,
                #     'retry_login': login_infos.retry_login,
                #     'block_count': login_infos.block_count,
                # }
                if login_infos.retry_login == 0:
                    login_infos.is_block = 'Y'
                    login_infos.save()
                    if login_infos.block_count >= self.MAX_BLOCK_COUNT:
                        # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
                        context = {
                            'remaining_time_in_seconds': remaining_time_in_seconds,
                            'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
                            'retry_login': login_infos.retry_login,
                            'block_count': login_infos.block_count,
                            'has_waiting_time': True,
                        }
                        print("콘텍스트 출력6 ", context)
                    else:
                        login_infos.block_count += 1
                        # context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요."
                        context = {
                            'remaining_time_in_seconds': remaining_time_in_seconds,
                            'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
                            'retry_login': login_infos.retry_login,
                            'block_count': login_infos.block_count,
                            # 'has_waiting_time': True
                        }
                        print("콘텍스트 출력7 ", context)
                                
                login_infos.save()
                # context['warning'] = "비밀번호가 일치하지 않습니다."
                context = {
                    'remaining_time_in_seconds': remaining_time_in_seconds,
                    'warning': "비밀번호가 일치하지 않습니다.",
                    'retry_login': login_infos.retry_login,
                    'block_count': login_infos.block_count,
                }
                print("콘텍스트 출력8 ", context)

        elif pw_checked:
                login_infos.retry_login = 5
                login_infos.is_block = 'N'
                login_infos.save()
                context = {'reservation': reservations}
                print("콘텍스트 출력5 ", context)
        


        return render(request, self.template_name, context)


        #     # 나중에 테스트끝나고 minutes 10으로 변경할것...
        #     if now - login_infos.last_login_date < timedelta(minutes=1):
        #         if login_infos.block_count >= self.MAX_BLOCK_COUNT:
        #             context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
        #         else:
        #             context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
        #         return render(request, self.template_name, context)
        #     elif login_infos.block_count < self.MAX_BLOCK_COUNT:
        #         login_infos.retry_login = 5
        #         login_infos.is_block = 'N'
        #         login_infos.block_count += 1
        #         login_infos.save()
        #     else:
        #         context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
        #         return render(request, self.template_name, context)



        # # 재시도횟수(retry_login) 증감
        # if pw_checked:
        #     login_infos.retry_login = 5  # 비밀번호가 일치하면 retry_login을 5로 재설정
        #     login_infos.is_block = 'N'  # 비밀번호가 일치하면 블록 상태를 해제
        #     login_infos.save()  # 변경된 retry_login 값을 저장

        #     context = {'reservation': reservations}
        #     return render(request, self.template_name, context)
        # else:
        #     # 비밀번호 불일치
        #     # 남은시간표시
        #     remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)


        #     login_infos.retry_login -= 1
        #     login_infos.last_login_date = datetime.now()

        #     if login_infos.retry_login == 0:
        #         login_infos.is_block = 'Y'
        #         login_infos.save()

        #         if login_infos.block_count >= self.MAX_BLOCK_COUNT:
        #             context = {
        #                 'remaining_time_in_seconds': remaining_time_in_seconds,
        #                 'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
        #                 'retry_login': login_infos.retry_login,
        #                 'block_count': login_infos.block_count,
        #             }
        #             return render(request, self.template_name, context)
        #         else:
        #             login_infos.block_count += 1
        #             context = {
        #                 'remaining_time_in_seconds': remaining_time_in_seconds,
        #                 'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
        #                 'retry_login': login_infos.retry_login,
        #                 'block_count': login_infos.block_count,
        #             }
        #             return render(request, self.template_name, context)
                
        #     login_infos.save()
        #     context = {
        #         'remaining_time_in_seconds': remaining_time_in_seconds,
        #         'warning': "비밀번호가 일치하지 않습니다.",
        #         'retry_login': login_infos.retry_login,
        #         'block_count': login_infos.block_count,
        #     }

        # # context = {'reservation': reservations}
        # return render(request, self.template_name, context)
    


    def post(self, request):
        reservation = request.session.get('reservation')
        pw_checked = request.session.get('pw_checked')
        # input_user_pw = request.session.get('input_user_pw')

        try:
            # compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
            if pw_checked:
                reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
        except models.Reservation_user.DoesNotExist:
            return render(request, self.template_name, {'invalid_access': True})
        
        reservations.delete()  # 조회한 예약삭제
        url = reverse('reservation_deleted_view') + '#anchor4'
        return HttpResponseRedirect(url)




# ## 예약 조회 및 취소 (수정전)
# class DetailView(View):
#     template_name = 'calendar_app/reservation_detail.html'
#     MAX_BLOCK_COUNT = 3  # 재시도 횟수 상수화

#     # 남은시간 계산
#     def calculate_remaining_time(self, last_login_date, now):
#         remaining_time_in_seconds = int((last_login_date + timedelta(minutes=1) - now).total_seconds())  # 남은 시간(초) 계산
#         return 0 if remaining_time_in_seconds < 0 else remaining_time_in_seconds

#     def get(self, request):
#         now = datetime.now()
#         reservation = request.session.get('reservation')
#         input_user_pw = request.session.get('input_user_pw')

#         try:
#             reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#         except models.Reservation_user.DoesNotExist:
#             messages.error(request, "예약 정보가 존재하지 않습니다.")
#             return render(request, self.template_name)

#         login_infos, created = models.Login_try.objects.get_or_create(user_id=reservations)
        

#         # 정지여부(is_block), 정지횟수(block_count) 확인
#         if login_infos.is_block == 'Y':
#             # 남은시간표시
#             remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)

#             context = {
#                 'remaining_time_in_seconds': remaining_time_in_seconds,
#                 'warning': None,
#                 'retry_login': login_infos.retry_login,
#                 'block_count': login_infos.block_count,
#             }

#             # 나중에 테스트끝나고 minutes 10으로 변경할것...
#             if now - login_infos.last_login_date < timedelta(minutes=1):
#                 if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                     context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다. 업체에 문의해주세요."
#                 else:
#                     context['warning'] = "로그인 시도를 너무 많이 하셨습니다. 잠시 후에 다시 시도해주세요."
#                 return render(request, self.template_name, context)
#             elif login_infos.block_count < self.MAX_BLOCK_COUNT:
#                 login_infos.retry_login = 5
#                 login_infos.is_block = 'N'
#                 login_infos.block_count += 1
#                 login_infos.save()
#             else:
#                 context['warning'] = "비밀번호 재시도 횟수를 초과하였습니다."
#                 return render(request, self.template_name, context)
#                 # 원래코드...테스트
#                 # url = reverse('find_reservation') + '#anchor1'
#                 # return HttpResponseRedirect(url)
            

#         # 암호비교
            
#         # 예외처리- 값이 비어있는 경우
#         if not input_user_pw or not reservation['pwhash']:
#             context = {
#                 'remaining_time_in_seconds': self.calculate_remaining_time(login_infos.last_login_date, now),
#                 'warning': "비밀번호가 일치하지 않습니다.",
#                 'retry_login': login_infos.retry_login,
#                 'block_count': login_infos.block_count,
#             }
#             return render(request, self.template_name, context)
        
#         print('1: ', input_user_pw.encode('utf-8'))
#         print('2: ', reservation['pwhash'].encode('utf-8'))
#         compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
#         print('해시비교', compare)


#         # 재시도횟수(retry_login) 증감
#         if compare:
#             login_infos.retry_login = 5  # 비밀번호가 일치하면 retry_login을 5로 재설정
#             login_infos.is_block = 'N'  # 비밀번호가 일치하면 블록 상태를 해제
#             login_infos.save()  # 변경된 retry_login 값을 저장

#             context = {'reservation': reservations}
#             return render(request, self.template_name, context)
#         else:
#             # 비밀번호 불일치
#             # 남은시간표시
#             remaining_time_in_seconds = self.calculate_remaining_time(login_infos.last_login_date, now)


#             login_infos.retry_login -= 1
#             login_infos.last_login_date = datetime.now()

#             if login_infos.retry_login == 0:
#                 login_infos.is_block = 'Y'
#                 login_infos.save()

#                 if login_infos.block_count >= self.MAX_BLOCK_COUNT:
#                     context = {
#                         'remaining_time_in_seconds': remaining_time_in_seconds,
#                         'warning': "비밀번호 재시도 횟수를 초과하였습니다.",
#                         'retry_login': login_infos.retry_login,
#                         'block_count': login_infos.block_count,
#                     }
#                     return render(request, self.template_name, context)
#                 else:
#                     login_infos.block_count += 1
#                     context = {
#                         'remaining_time_in_seconds': remaining_time_in_seconds,
#                         'warning': "비밀번호 재시도 횟수를 초과하였습니다. 10분 후에 다시 시도해주세요.",
#                         'retry_login': login_infos.retry_login,
#                         'block_count': login_infos.block_count,
#                     }
#                     return render(request, self.template_name, context)
                
#             login_infos.save()
#             context = {
#                 'remaining_time_in_seconds': remaining_time_in_seconds,
#                 'warning': "비밀번호가 일치하지 않습니다.",
#                 'retry_login': login_infos.retry_login,
#                 'block_count': login_infos.block_count,
#             }

#         # context = {'reservation': reservations}
#         return render(request, self.template_name, context)
    


#     def post(self, request):
#         reservation = request.session.get('reservation')
#         input_user_pw = request.session.get('input_user_pw')

#         try:
#             compare = bcrypt.checkpw(input_user_pw.encode('utf-8'), reservation['pwhash'].encode('utf-8'))
#             if compare:
#                 reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'])
#         except models.Reservation_user.DoesNotExist:
#             return render(request, self.template_name, {'invalid_access': True})
        
#         reservations.delete()  # 조회한 예약삭제
#         url = reverse('reservation_deleted_view') + '#anchor4'
#         return HttpResponseRedirect(url)





# 취소후 화면
class ReservationDeletedView(View):
    template_name = 'calendar_app/reservation_deleted.html'

    def get(self, request):
        return render(request, self.template_name)