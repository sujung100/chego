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
            rst_user.visitor_num = int(request.POST["v_num"])
            rst_user.password = request.POST["password"]
            rst_user.store_id = sto

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
            return HttpResponse("해당하는 예약 정보가 없습니다.")

        request.session['reservation'] = model_to_dict(reservation)  # model_to_dict: dict로 변환

        return redirect('input_user_pw')
    
# 본인확인
class InputUserNameView(View):
    def get(self, request):
        return render(request, 'calendar_app/input_user_pw.html')

    def post(self, request):
        input_pw = request.POST.get('input_pw')
        request.session['input_user_pw'] = input_pw
        return redirect('detail_view')
    
# 예약조회
# class DetailView(View):
#     template_name = 'calendar_app/reservation_detail.html'

#     def get(self, request):
#         reservation = request.session.get('reservation')
#         input_pw = request.session.get('input_user_pw')

#         if reservation is None or input_pw != reservation['password']:
#             return HttpResponse("입력하신 비밀번호가 틀렸습니다.")
        
#         store_name = models.Store.objects.get(id=reservation['store_id']).store_name
#         reservation['store_name'] = store_name

#         return render(request, self.template_name, reservation)



# # 예약 조회 및 삭제 테스트
# class DetailView(View):
#     template_name = 'calendar_app/reservation_detail.html'

#     def get(self, request):
#         reservation = models.Reservation_user.objects.get(password=request.session.get('input_user_pw'))
#         input_user_name = request.session.get('input_user_pw')

#         if reservation is None or input_user_name != reservation.password:
#             return HttpResponse("예약 정보가 없거나, 입력하신 사용자 이름이 예약자와 일치하지 않습니다.")

#         store_name = models.Store.objects.get(id=reservation.store_id_id).store_name
#         context = {
#             'reservation': reservation,
#             'store_name': store_name
#         }

#         return render(request, self.template_name, context)

#     def post(self, request):
#         reservation = models.Reservation_user.objects.get(password=request.session.get('input_user_pw'))
#         reservation.delete()  # Delete the reservation
#         return redirect('reservation_deleted_view')  # Redirect to a view that shows a message about the deletion
    

# class ReservationDeletedView(View):
#     template_name = 'calendar_app/reservation_deleted.html'

#     def get(self, request):
#         return render(request, self.template_name)



# # 예약 조회 및 삭제 테스트
# class DetailView(View):
#     template_name = 'calendar_app/reservation_detail.html'

#     def get(self, request):
#         input_user_pw = request.session.get('input_user_pw')
#         reservations = models.Reservation_user.objects.filter(password=input_user_pw).select_related('store_id')
#         # Q하기-필터로 조건두개

#         if not reservations:
#             return HttpResponse("예약 정보가 없거나, 입력하신 사용자 이름이 예약자와 일치하지 않습니다.")

#         context = {
#             'reservations': reservations
#         }

#         return render(request, self.template_name, context)

#     def post(self, request):
#         input_user_pw = request.session.get('input_user_pw')
#         reservations = models.Reservation_user.objects.filter(password=input_user_pw)
#         reservations.delete()  # Delete the reservation
#         return redirect('reservation_deleted_view')  # Redirect to a view that shows a message about the deletion
    

# class ReservationDeletedView(View):
#     template_name = 'calendar_app/reservation_deleted.html'

#     def get(self, request):
#         return render(request, self.template_name)




# 예약 조회 및 삭제 테스트2
class DetailView(View):
    template_name = 'calendar_app/reservation_detail.html'

    def get(self, request):
        reservation = request.session.get('reservation')
        input_user_pw = request.session.get('input_user_pw')

        try:
            reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'], password=input_user_pw)
        except models.Reservation_user.DoesNotExist:
            return HttpResponse("예약 정보가 존재하지 않습니다.")
        
        context = {'reservation': reservations}
        return render(request, self.template_name, context)
    

    def post(self, request):
        reservation = request.session.get('reservation')
        input_user_pw = request.session.get('input_user_pw')
        reservations = models.Reservation_user.objects.select_related('store_id').get(id=reservation['id'], password=input_user_pw)
        reservations.delete()  # 조회한 예약삭제
        return redirect('reservation_deleted_view')
    

class ReservationDeletedView(View):
    template_name = 'calendar_app/reservation_deleted.html'

    def get(self, request):
        return render(request, self.template_name)