from django.shortcuts import render
from django.views.generic import TemplateView
from reservation import models

from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.http import HttpResponseRedirect
from django.urls import reverse


# class Idx_list(ListView):
#     model = models.Store
#     template_name = "reservation/main4.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         store_list = context['object_list']

#         store_times_dict = {}
#         store_time_date = []
#         for store in store_list:
#             store_times = models.Store_times.objects.filter(store_id=store.pk)
#             store_times_dict[store.pk] = store_times


#         context['store_times_dict'] = store_times_dict
#         return context


    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     store_list = models.Store.objects.all()
    #     context['store_list'] = store_list

    #     store_times_dict = {}
    #     for store in store_list:
    #         store_times = models.Store_times.objects.filter(store_id=store.pk)
    #         store_times_dict[store.pk] = store_times
    #     context['store_times_dict'] = store_times_dict

    #     pk = self.kwargs.get('pk')
    #     store = get_object_or_404(models.Store, pk=pk) if pk else store_list.first()
    #     context['store'] = store
    #     sto_time = models.Store_times.objects.filter(store_id=store.pk)

    #     store_dates = []
    #     for dates in sto_time:
    #         dates_info  = models.Reservation_user.objects.filter(
    #         Q(store_id=store) &
    #         Q(user_time=dates.reservation_time) 
    #         )

    #         user_dates = [info.reservation_date for info in dates_info]
    #         store_dates.append({
    #         'user_date': user_dates,
    #         'disable_time': json.dumps([info.user_time for info in dates_info ])
    #         })
    #     context['sto_time'] = sto_time
    #     context['store_dates_json'] = json.dumps(store_dates, cls=DjangoJSONEncoder)
    #     return context
class Idx_list(TemplateView):
    template_name = "reservation/main4.html"
    
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
            return HttpResponseRedirect(reverse('main4'))

        return self.get(request, *args, **kwargs)




def Idx(request):
    return render(request,"reservation/index.html")