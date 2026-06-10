from django.shortcuts import render, redirect, get_object_or_404
from calendar_app import models as rsv

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, ListView, UpdateView, FormView
from django.contrib.auth import login, authenticate
from django.core.exceptions import ValidationError, PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect

from django.http import JsonResponse, QueryDict, HttpRequest, HttpResponse
from django.views import View
from django.core.paginator import Paginator
from django.core import serializers
from collections import defaultdict
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.db.models.functions import Substr
from . import models

from datetime import datetime
from dateutil.relativedelta import relativedelta

from .forms import ManagerUpdateForm, StoreUpdateForm, UpdateForm, TotalReservationForm

# 테스트중 24.10.28
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# 예약조회 - 검색기능 - 전화번호 조회시 기호제거
from django.db.models import F, Func, Value, CharField
from django.db.models.functions import Replace

from django.http import HttpResponseForbidden
from urllib.parse import urlencode


ADMIN_USERS = { "admin" : True,}


def store_list(request):
    return render(request, "manager/manager_index.html")

def production_current_user(request):
    current_user = request.user
    if not current_user.is_authenticated:
        return JsonResponse([], safe=False)

# class ManagerStoreList(LoginRequiredMixin, ListView, LoginView, FormView):
class ManagerStoreList(LoginRequiredMixin, ListView):
    model = rsv.Store
    template_name = "manager/manager_sung_index.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("index")
    login_url = reverse_lazy("login")

    # def get(self, request):
    #     todos = rsv.Todo.objects.all().values('id', 'text', 'complete')
    #     return JsonResponse(list(todos), safe=False, status=200)

    def get_queryset(self):
        current_user = self.request.user
        if current_user.is_authenticated:
            # manager = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)[:3]
            manager = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)
        else:
            manager = rsv.Store.objects.none()
        return manager

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = self.request.user
        print("커런트유저", current_user)
        context["username"] = current_user.username if current_user.is_authenticated else None
        for admin_user in ADMIN_USERS.keys():
            context["adminusers"] = admin_user

        context['manager'] = self.get_queryset()
        # print(context['manager'])
        manager_list_dicts = [model_to_dict(manager) for manager in self.get_queryset()]
        
        context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)

        if current_user.is_authenticated:
            
            # 3개월 예약추이 차트 
            today = timezone.now().date()
            target_months = [(today - relativedelta(months=i)).strftime('%Y-%m') for i in range(3)]
            month_filter = Q()
            for month in target_months:
                month_filter |= Q(reservation_date__startswith=month)

            rsv_stats_queryset = rsv.Reservation_user.objects.filter(
                store_id__owner=current_user 
            ).filter(
                month_filter 
            ).annotate(
                res_month=Substr('reservation_date', 1, 7)
            ).values(
                'store_id', 'res_month'
            ).annotate(
                total_count=Count('id')
            ).order_by('store_id', 'res_month')

            # 월 예약수 - 스토어기준
            stats_list = list(rsv_stats_queryset)
            context["rsv_month_json"] = json.dumps(stats_list, cls=DjangoJSONEncoder)
            
            print(f"타겟월: {target_months}")
            print(f"결과 갯수: {rsv_stats_queryset.count()}")
            print("월예약수", context["rsv_month_json"])

            rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
            messages = models.Message.all_messages(current_user.username)
            context["rsvs"] = rsvs
            context["messages"] = messages
            sto_info = list(rsv.Store.objects.filter(owner=current_user).values('store_name', 'address'))
            sto_json = json.dumps(sto_info)
            context["sto_json"] = sto_json

            # 시간대 차트
            # 시간대별 예약 건수(user_time 그룹화)
            time_stats = (
                rsv.Reservation_user.objects
                .values('store_id', 'user_time')
                .annotate(count=Count('id'))
                .order_by('user_time')
            )
            time_chart_raw = list(time_stats)
            context['time_chart_raw'] = json.dumps(time_chart_raw)
            # context['time_labels'] = json.dumps([item['user_time'] for item in time_stats])
            # context['time_data'] = json.dumps([item['count'] for item in time_stats])
            # print("타임라벨", context['time_labels'])
            # print("타임데이터", context['time_data'])
            print()
            print("타임데이터", context['time_chart_raw'])
            print()

            # 리드타임 차트
            all_reservations = rsv.Reservation_user.objects.all()
            lead_chart_raw = []
            
            for r in all_reservations:
                if not r.reservation_date or not r.date:
                    continue
                    
                try:
                    # [중요] DB에 저장된 reservation_date 문자열의 포맷에 맞게 수정하세요.
                    # 예: "2026-05-18" -> "%Y-%m-%d" / "2026.05.18" -> "%Y.%m.%d"
                    rsv_date = datetime.strptime(r.reservation_date.strip(), "%Y-%m-%d").date()
                    create_date = r.date.date() # DateTimeField를 Date 객체로 변환
                    
                    # 실제 방문일 - 예약 등록일 (며칠 전 예약했는지 계산)
                    lead_day = (rsv_date - create_date).days
                    
                    # 오늘 등록해서 오늘 방문하는 경우 등 예외 처리
                    if lead_day < 0: 
                        lead_day = 0
                        
                    lead_chart_raw.append({
                        'store_id': r.store_id_id,
                        'lead_day': lead_day # 💡 숫자로 전달하여 JS에서 구간 분류를 처리합니다.
                    })
                except Exception as e:
                    # 날짜 형식이 안 맞아서 에러가 나는 데이터는 스킵
                    continue

            context['time_chart_raw'] = json.dumps(list(time_stats)) # 기존 데이터
            context['lead_chart_raw'] = json.dumps(lead_chart_raw)   # 신규 리드타임 데이터
        
        return context
    
    # 얘 나중에 빼도되나 확인-- post요청 딱히 보내고있지않음 (투두리스트는 아래의 TodoAPI의 post에서 수행)
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.method == 'POST':
                # print("안돼야 되잖아")
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
    

class TodoAPI(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        todos = rsv.Todo.objects.all().values('id', 'text', 'complete')
        return JsonResponse(list(todos), safe=False)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            todo_list = data.get('todos', [])

            # 1. 기존 데이터를 지웁니다. 
            # (실제 서비스라면 .filter(user=request.user).delete() 처럼 본인 것만 지워야 합니다)
            rsv.Todo.objects.all().delete()

            # 2. 새로 저장합니다.
            new_todo_objs = []
            for item in todo_list:
                new_todo_objs.append(rsv.Todo(
                    text=item['text'],
                    complete=item.get('complete', False)
                    # 여기서 id는 넣지 않습니다. DB가 새로 부여하도록 합니다.
                ))
            
            rsv.Todo.objects.bulk_create(new_todo_objs)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    

# 기존
# class StoreTimesView(View):
#     def get(self, request):
#         current_user = request.user

#         if current_user.is_authenticated:
#             stores = rsv.Store.objects.filter(owner=current_user, store_name__isnull=False)[:3]

#             query_dict = QueryDict(request.META['QUERY_STRING'])
#             requested_store_id = query_dict.get('store_id', None)

#             data = []
#             for store in stores:
#                 if requested_store_id is not None and str(store.id) != requested_store_id:
#                     continue
                
#                 rsv_users = rsv.Reservation_user.objects.filter(store_id=store)
#                 data.append([model_to_dict(rsv_user) for rsv_user in rsv_users])

#             return JsonResponse(data, safe=False)
#         else:
#             return JsonResponse([], safe=False)


# 수정중 26.06.09
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
                
                rsv_users = rsv.Reservation_user.objects.filter(store_id=store, reservation_check=False)
                data.append([model_to_dict(rsv_user) for rsv_user in rsv_users])

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse([], safe=False)


class UserInfo(View):
    def get(self, request):
        current_user = request.user
        if not current_user.is_authenticated:
            return JsonResponse([], safe=False)
        usernames = list(User.objects.filter(is_superuser=False).values_list('username', flat=True))
        response = {
            "user_names" : usernames,
            "current_user" : current_user.username,
        }
        return JsonResponse(response, safe=False)

class ChatRoom(View):
    def get(self, request):
        # 인증된 사용자인지 확인
        current_user = request.user
        if not current_user.is_authenticated:
            return JsonResponse([], safe=False)

        # 쿼리 파라미터에서 chatroom 값을 가져옴
        # chatroom_name = request.GET.get('chatroom', None)

        # # chatroom 값이 제공되었다면 해당 채팅방만 필터링, 그렇지 않다면 모든 채팅방 반환
        # if chatroom_name:
        #     chatrooms = models.Message.objects.filter(chatroom=chatroom_name)
        #     print("트라이",chatrooms)
        # else:
        #     chatrooms = models.Message.latest_messages()
        #     print("엘스",chatrooms)

        # 채팅방 정보를 JSON 형식으로 변환
        data = []
        chatrooms = models.Message.latest_messages()
        
        
        for chatroom in chatrooms:
            # print(chatroom)
            formatted_time = chatroom["recent_timestamp"].strftime('%Y-%m-%d %H:%M')
            unread_count = models.Message.unread_messages(chatroom["chatroom"])  # 채팅방별로 읽지 않은 메시지의 수를 구함
            data.append({
                "chatroom" : chatroom["chatroom"],
                "recent_content" : chatroom["recent_content"],
                "timestamp" : formatted_time,
                "unread_messages" : unread_count,
                
            })

        return JsonResponse(data, safe=False)
        
class EnterChatRoom(View):

    def get_queryset(self):
        # 원하는 쿼리셋을 반환하는 로직을 여기에 작성하세요.
        return self.model.objects.all()

    def get_messages(self, chatroom_name, page_number):
        # 원하는 메시지를 반환하는 로직을 여기에 작성하세요.
        return models.Message.all_messages(chatroom_name, page_number)

    


    # print("이거 찍히냐",get_messages())
    def get(self, request, chatroom_name,):
        # 인증된 사용자인지 확인
        current_user = request.user
        if not current_user.is_authenticated:
            return JsonResponse([], safe=False)
        page_number = int(request.GET.get("page_number", 1))
        messages = self.get_messages(chatroom_name, page_number)
        # print(messages)
        # 해당 채팅방의 모든 메시지를 가져옴
        # messages = models.Message.objects.filter(chatroom=chatroom_name)
        # print("메시지 가져와 지냐", messages)
        # 메시지 정보를 JSON 형식으로 변환
        data = [model_to_dict(message) for message in messages]
        # print("겟 메세지",data)
        for message, message_dict in zip(messages, data):
            formatted_time = message.timestamp.strftime('%Y-%m-%d %H:%M')
            message_dict["timestamp"] = formatted_time

        unread_count = models.Message.unread_messages(chatroom_name)
        # message_dict["unread_messages"] = unread_count
        response = {
            "messages" : data,
            "unread_messages" : unread_count,
        }

        return JsonResponse(response, safe=False)



class Reservation_Details(View):
    # def rsv_check(self, user_id):
    #     queryset = rsv.Reservation_user.objects.filter(store_id__owner_id=user_id)
    #     return serializers.serialize("python", queryset, fields=("reservation_check"))

    def rsv_check(self, user_id):
        queryset = rsv.Reservation_user.objects.filter(store_id__owner_id=user_id,  reservation_check=False)
        serialized_data = serializers.serialize("python", queryset, fields=("reservation_check"))
        return len(serialized_data)

    def get(self, request, rsv_id=None):
        user_id = request.user.id
        production_current_user(request)
        if rsv_id:
            # rsv_model = get_object_or_404(rsv.Reservation_user.objects.defer("pwhash"), id=rsv_id)
            rsv_model = get_object_or_404(rsv.Reservation_user, id=rsv_id)
            rsv_dict = model_to_dict(rsv_model)
            rsv_dict.pop("pwhash", None)
            rsv_dict["rsv_check"] = self.rsv_check(user_id)
            print("이프", rsv_dict)
            return JsonResponse(rsv_dict)
            
        else:
            # print(user_id)
            rsv_model = rsv.Reservation_user.objects.defer("pwhash").filter(store_id__owner_id=user_id, reservation_check=False)
            # print("Reservation_Details 엘스", rsv_model)
            rsv_dict = [model_to_dict(r) for r in rsv_model]
            for r in rsv_dict:
                r.pop("pwhash", None)
                r["rsv_check"] = self.rsv_check(user_id)
            # print("엘스", rsv_dict)
            return JsonResponse(rsv_dict, safe=False)



# 통합 - 달력 + 예약조회페이지
# class Total_Reservation_Check(TemplateView):
class Total_Reservation_Check(LoginRequiredMixin, UpdateView):
    model = rsv.Store
    form_class = TotalReservationForm
    template_name = 'manager/manager_store_detail.html'

    def dispatch(self, request, *args, **kwargs):
        # store_id = self.kwargs['store_id']
        store_id = self.kwargs['pk']
        store = get_object_or_404(rsv.Store, pk=store_id)
        if self.request.user.id != store.owner_id:
            return HttpResponseForbidden("접근권한이 없습니다.")
        return super().dispatch(request, *args, **kwargs)
    

    def get_context_data(self, **kwargs):
        # store_id = self.kwargs['store_id']
        store_id = self.kwargs['pk']
        store = get_object_or_404(rsv.Store, pk=store_id)
        manager = rsv.Manager.objects.get(user=self.request.user)
        context = super().get_context_data(**kwargs)
        context['manager'] = manager
        context['store'] = store

        # if self.request.user.id != store.owner_id :
        #     return HttpResponseForbidden("접근권한이 없습니다.")
        
        # context = super(Total_Reservation_Check, self).get_context_data(**kwargs)
        # context['form'] = ManagerUpdateForm(instance=self.manager)
        # context['form_store'] = StoreUpdateForm(instance=self.store)

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

        reservations = rsv.Reservation_user.objects.annotate(
            user_phone_without_hyphen=Replace('user_phone', Value('-'), Value(''), output_field=CharField())
        ).filter(
            # Q(store_id=store) if store else Q(),
            Q(user_name__icontains=name) if name else Q(),
            Q(user_phone_without_hyphen__icontains=phone_without_hyphen) if phone else Q(),
            date_filter if kw else Q(),
            store_id=store
        ).distinct()

        # 10.15 수정전
        # paginator = Paginator(reservations, 5)
        # page_number = self.request.GET.get('page')
        # page_obj = paginator.get_page(page_number)

        # context['page_obj'] = page_obj
        # context['kw'] = kw


        # 수정중
        # 첫 번째 페이지네이션
        first_pgt = Paginator(reservations, 5)
        first_num = self.request.GET.get('first_page')
        first_obj= first_pgt.get_page(first_num)

        # 두 번째 페이지네이션
        second_pgt = Paginator(reservations, 5)
        second_num = self.request.GET.get('second_page')
        second_obj = second_pgt.get_page(second_num)

        context['1st_obj'] = first_obj
        context['2nd_obj'] = second_obj
        context['kw'] = kw



        # 달력
        store_time = rsv.Store_times.objects.filter(store_id=store_id)
        user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

        user_dates = []
        dates_list = [date.reservation_date for date in user_time]
        user_dates.append({
            "user_dates" : dates_list
        })
        context["user_dates_json"] = json.dumps(dates_list, cls=DjangoJSONEncoder)



        input1 = self.request.GET.get('name', '')
        input2 = self.request.GET.get('phone', '')
        input3 = self.request.GET.get('kw', '')

        # 각 입력값에 따라 CSS 클래스를 설정
        context['css_class1'] = 'active' if input1 else ''
        context['css_class2'] = 'active' if input2 else ''
        context['css_class3'] = 'active' if input3 else ''

        context['input1'] = input1
        context['input2'] = input2
        context['input3'] = input3
        context['request'] = self.request
        context["username"] = self.request.user.username

        

        return context
    

    def post(self, request, *args, **kwargs):
        # URL에서 pk값 가져오기
        requested_store_id = self.kwargs.get('pk')
        # Store테이블의 id값을 가진 객체찾기 (url에서 가져온 store_id값과 일치하는)
        store = get_object_or_404(rsv.Store, pk=requested_store_id)
        
        if store:
            # post요청
            if request.method == 'POST':
                 # 전달받은 rsv_ids를 리스트로 변환
                rsv_ids = request.POST.getlist('rsv_ids')
                # print("Requested rsv_ids찍어봐라:", rsv_ids)

                # rsv_ids를 정수형으로 변환
                rsv_ids = [int(id) for id in rsv_ids]

                # 해당 ID를 가진 예약 삭제
                rsv.Reservation_user.objects.filter(id__in=rsv_ids, store_id=store.pk).delete()

                # POST 요청 시 입력값을 가져오기
                input1 = self.request.GET.get('name', '')
                input2 = self.request.GET.get('phone', '')
                input3 = self.request.GET.get('kw', '')
                qs = urlencode({'name': input1, 'phone': input2, 'kw': input3})
                # print("찍어봐아아아", qs)

                # 쿼리 매개변수로 입력값을 전달하여 리다이렉트
                # return redirect(f"{reverse('store_detail')}?input1={input1}&input2={input2}&input3={input3}", pk=store.pk)
                return redirect(reverse('store_detail', kwargs={'pk': store.pk}) + '?' + qs)
                

                # 10.21 수정
                # 성공 후 리다이렉트
                # return redirect('store_detail', pk=store.pk)
                


        return self.get(request, *args, **kwargs)
    

    
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



class Write(View):
    def get(self, request):
        current_user = request.user

        if current_user.is_authenticated:
            stores = list(rsv.Store.objects.filter(owner=current_user, store_name__isnull=False).values_list('id', 'store_name'))
            # print("스토어들", stores)
            context = {
                "stores_json" : mark_safe(json.dumps(stores)),
            }
            return render(request, 'manager/manager_write.html', context)
        else:
            raise PermissionDenied

    def post(self, request, *args, **kwargs):
        sto = rsv.Store()
        # print(atc.title)
        sto.store_name = request.POST["store_name"]
        # 주소
        addr = request.POST.get("sample6_address", "")
        detail = request.POST.get("sample6_detailAddress")
        extra = request.POST.get("sample6_extraAddress")
        full_address = " ".join(filter(None, [addr, detail, extra]))

        sto.address = full_address
        sto.owner = request.user
        print("사용자", request.user)
        sto.save()

    # 폼재전송 방지용 PRG패턴 post -> redirect -> get
        return redirect('write')


# def write(request):
   
#     if request.method == 'POST':
#         sto = rsv.Store()
#         # print(atc.title)
#         sto.store_name = request.POST["store_name"]
#         # 주소
#         addr = request.POST.get("sample6_address", "")
#         detail = request.POST.get("sample6_detailAddress")
#         extra = request.POST.get("sample6_extraAddress")
#         full_address = " ".join(filter(None, [addr, detail, extra]))

#         sto.address = full_address
#         sto.owner = request.user
#         print("사용자", request.user)
#         sto.save()


#     # 폼재전송 방지용 PRG패턴 post -> redirect -> get
#         return redirect('write')
#     else:
#         # GET 요청 처리 (폼을 보여주는 경우)
#         return render(request, 'manager/manager_write.html')


def test_chat(request):
    return render(request, "manager/test/test_chat.html")

@login_required
def test_room(request, room_name):
    context = {
        "room_name_json" : mark_safe(json.dumps(room_name)),
        "username" : request.user.username,
    }
    return render(request, "manager/test/test_room.html", context)

def admin_chat(request):
    context = {
        "username" : request.user.username,
    }
    return render(request, "manager/test/admin_chat.html", context)
    # return render(request, "manager/admin_chat2.html", context)

def admin_chat2(request):
    context = {
        "username" : request.user.username,
    }
    # return render(request, "manager/test/admin_chat.html", context)
    return render(request, "manager/admin_chat2.html", context)

class AdminChat2(ListView):
    model = models.Message
    template_name = "manager/admin_chat2.html"
    def get_queryset(self):
        # 원하는 쿼리셋을 반환하는 로직을 여기에 작성하세요.
        return self.model.objects.all()

    def get_messages(self, username):
        # 원하는 메시지를 반환하는 로직을 여기에 작성하세요.
        return models.Message.all_messages(username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        context["username"] = current_user.username if current_user.is_authenticated else None
        for admin_user in ADMIN_USERS.keys():
            context["adminusers"] = admin_user

        context['manager'] = self.get_queryset()

        manager_list_dicts = [model_to_dict(manager) for manager in context['manager']]
        
        context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)
        if current_user.is_authenticated:
            rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
            messages = self.get_messages(current_user.username)
            context["rsvs"] = rsvs
            context["messages"] = messages
        return context
    


# 기본 예약조회
# class ManagerStoreUpdateView(LoginRequiredMixin, FormView):
#     template_name = 'manager/manager_operate.html'
#     form_class = ManagerUpdateForm
#     store_form_class = StoreUpdateForm

#     # 권한설정
#     def dispatch(self, request, *args, **kwargs):
#         self.manager = get_object_or_404(rsv.Manager, pk=kwargs['pk'])
#         self.store = get_object_or_404(rsv.Store, pk=kwargs['store_id'])
        
#         # 조건3개
#         if request.user.is_authenticated and request.user == self.manager.user and self.manager.user == self.store.owner:
#             return super(ManagerStoreUpdateView, self).dispatch(request, *args, **kwargs)
#         else:
#             raise PermissionDenied


#     def get_context_data(self, **kwargs):
#         context = super(ManagerStoreUpdateView, self).get_context_data(**kwargs)
#         context['form'] = ManagerUpdateForm(instance=self.manager)
#         context['form_store'] = StoreUpdateForm(instance=self.store)
#         context['manager'] = self.manager
#         context['store'] = self.store


#         name = self.request.GET.get('name')
#         phone = self.request.GET.get('phone')
#         kw = self.request.GET.get('kw')
        
#         date_filter = Q()
#         if kw:
#             try:
#                 datetime.strptime(kw, '%Y-%m-%d')
#                 date_filter = Q(reservation_date__icontains=kw)
#             except ValueError:
#                 try:
#                     datetime.strptime(kw, '%Y-%m')
#                     date_filter = Q(reservation_date__icontains=kw)
#                 except ValueError:
#                     date_filter = Q(reservation_date__startswith=kw)
                    
#         phone_without_hyphen = phone.replace("-", "") if phone else None

#         reservations = rsv.Reservation_user.objects.annotate(
#             user_phone_without_hyphen=Replace('user_phone', Value('-'), Value(''), output_field=CharField())
#         ).filter(
#             Q(user_name__icontains=name) if name else Q(),
#             Q(user_phone_without_hyphen__icontains=phone_without_hyphen) if phone else Q(),
#             date_filter if kw else Q(),
#             store_id=self.store
#         ).distinct()

#         paginator = Paginator(reservations, 10)
#         page_number = self.request.GET.get('page')
#         page_obj = paginator.get_page(page_number)

#         context['page_obj'] = page_obj
#         context['kw'] = kw

#         print("전체 콘텍스트 출력: ", context)

#         return context

#     def form_valid(self, form):
#         manager_form = form
#         store_form = self.store_form_class(self.request.POST, instance=self.store)

#         if manager_form.is_valid() and store_form.is_valid():
#             manager_form.save()
#             store_form.save()
#             return HttpResponseRedirect(reverse('success_page'))
#         else:
#             return self.form_invalid(form)

#     def form_invalid(self, form):
#         context = super(ManagerStoreUpdateView, self).get_context_data()
#         context['form'] = form
#         context['form_store'] = self.store_form_class(self.request.POST, instance=self.store)
#         return self.render_to_response(context)



# class Test123(LoginRequiredMixin, UpdateView):
#     model = rsv.Store
#     form_class = UpdateForm
#     template_name = 'manager/manager_update_form.html'

#     def get_object(self, queryset=None):
#         # self.kwargs에서 'store_id' 값을 가져와서 객체 조회
#         store_id = self.kwargs.get('store_id')
#         return get_object_or_404(rsv.Store, pk=store_id)
    


# 수정완 - pk하나로 변경
class Update(LoginRequiredMixin, UpdateView):
    model = rsv.Store
    form_class = UpdateForm
    template_name = 'manager/manager_update_form.html'
    # print("야 되냐")

    def setup_variables(self, store_id):
        # 공통 변수 설정
        if not hasattr(self, 'store'):
            self.store = get_object_or_404(rsv.Store, id=store_id)
        if not hasattr(self, 'store_time'):
            self.store_time = rsv.Store_times.objects.filter(store_id=store_id)
        if not hasattr(self, 'user_time'):
            self.user_time = rsv.Reservation_user.objects.filter(store_id=store_id)
    
    def get_object(self, queryset=None):
        # URL에서 store_id를 사용하여 Store 객체 찾기
        store_id = self.kwargs.get('store_id')
        return get_object_or_404(rsv.Store, id=store_id)

    def dispatch(self, request, *args, **kwargs):
        self.store = self.get_object()
        
        # 현재 로그인한 사용자가 Store의 owner와 일치하는지 확인
        if request.user.is_authenticated and request.user == self.store.owner:
            return super(Update, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied


    def get_context_data(self, **kwargs):
        # print("여긴 되냐")
        store_id = self.kwargs.get('store_id')
        self.setup_variables(store_id)
        
        request = self.request
        context = super().get_context_data(**kwargs)

        # URL에서 store_id값 가져오기
        requested_store_id = self.kwargs.get('store_id')
        # print("requested_store_id", requested_store_id)
        # print("찍어보자1", requested_store_id)

        # 해당 store_id를 가진 Store 객체 찾기
        # Store테이블의 id값찾기 (url에서 가져온 store_id값과 일치하는)
        # store = get_object_or_404(rsv.Store, pk=requested_store_id)
        store = get_object_or_404(rsv.Store, pk=requested_store_id)
        # print("여긴가3")

        if store:
            context['store'] = store
            dates_list = [date.reservation_date for date in self.user_time]
            # print("데이트리스트", dates_list)

            # Store의 owner(User 객체)와 연결된 Manager 찾기
            manager_of_the_store = rsv.Manager.objects.filter(user=store.owner).first()
            # print("찍어보자2", manager_of_the_store)
            
            if manager_of_the_store:
                context['manager'] = manager_of_the_store
                # print("스토어찍어", store)
                # print("스토어네임찍어", store.store_name)

            # Store의 pk값과 Store_times의 store_id값과 일치하는 Store_times 가져오기
            # sort_type : 매니저 시간설정 옵션 (null - 모든요일 동일)
            sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk, sort_type__isnull=True)
            # context['sto_time_objects'] = sto_time_objects
            context['sto_time_objects'] = json.dumps(list(sto_time_objects.values('reservation_time')), cls=DjangoJSONEncoder)

            wd_time_objects = rsv.Store_times.objects.filter(store_id=store.pk, sort_type='wd')
            # context['wd_time_objects'] = wd_time_objects
            context['wd_time_objects'] = json.dumps(list(wd_time_objects.values('reservation_time')), cls=DjangoJSONEncoder)

            wknd_time_objects = rsv.Store_times.objects.filter(store_id=store.pk, sort_type='wknd')
            # context['wknd_time_objects'] = wknd_time_objects
            context['wknd_time_objects'] = json.dumps(list(wknd_time_objects.values('reservation_time')), cls=DjangoJSONEncoder)

            # print("찍어보자3", sto_time_objects)
            # print("찍어보자3-1", sto_time_objects.values)
            # print("찍어보자3-2", wknd_time_objects)
            # print("찍어보자3-3", wknd_time_objects.values)
            # print("찍어보자3-4", wknd_time_objects)
            # print("찍어보자3-5", wknd_time_objects.values)
            
            sto_time_values_list  = {
                'store_id': store.pk,
                'sto_time': list(sto_time_objects.values()),
            }

            # print()
            # print("찍어보자4 ", sto_time_values_list)
            # print("찍어보자4길이 ", len(sto_time_objects))
            # print()

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
            # context['username'] = request.user.username
            # context['user_dates_json'] = json.dumps(dates_list, cls=DjangoJSONEncoder),

            context["user_dates_json"] = json.dumps(dates_list, cls=DjangoJSONEncoder)
            context["username"] = request.user.username
            print()
            print()
            # print("콘텍스트    ", context)
        return context
    
    # post요청 삭제 -> 웹소켓으로 db저장하도록 수정

# 달력 테스트
# @method_decorator(csrf_exempt, name="dispatch")
# class NewTest1(View):
#     template_name = "manager/test_sung1.html"
#     # template_name = "manager/manager_store_detail.html"
#     def setup_variables(self, store_id):
#         # 공통으로 사용되는 변수들을 설정합니다.
#         if not hasattr(self, 'store'):
#             self.store = get_object_or_404(rsv.Store, id=store_id)
#         if not hasattr(self, 'store_time'):
#             self.store_time = rsv.Store_times.objects.filter(store_id=store_id)
#         if not hasattr(self, 'user_time'):
#             self.user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

#     def get(self, request, store_id, *args, **kwargs):
#         self.setup_variables(store_id)

#         if not request.user.is_authenticated or request.user.id != self.store.owner_id:
#             return HttpResponseForbidden("접근 권한이 없습니다.")
        
#         dates_list = [date.reservation_date for date in self.user_time]
#         print("DT리스트", dates_list)
        
#         context = {
#             "user_dates_json": json.dumps(dates_list, cls=DjangoJSONEncoder),
#             "username": request.user.username
#         }

#         return render(request, self.template_name, context)
    
#     def post(self, request, store_id, *args, **kwargs):
#         self.setup_variables(store_id)

#         if not request.user.is_authenticated or request.user.id != self.store.owner_id:
#             return JsonResponse({"message": "접근 권한이 없습니다."}, status=403)

#         try:
#             data = json.loads(request.body)
#             self.store.start_rsv_possible = data.get("activate_date_start")
#             self.store.end_rsv_possible = data.get("activate_date_end")
#             self.store.full_clean()
#             self.store.save()
#         except json.JSONDecodeError:
#             return JsonResponse({"message": "유효하지 않은 JSON 형식입니다."}, status=400)
#         except ValidationError as e:
#             # 유효성 검사 실패 시 에러
#             error_message = str(e)
#             return HttpResponse(error_message, status=400)


#         return JsonResponse({"message": "성공적으로 처리되었습니다."}, status=200)



    
