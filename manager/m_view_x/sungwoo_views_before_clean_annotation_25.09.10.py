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
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from . import models

from datetime import datetime

from .forms import ManagerUpdateForm, StoreUpdateForm, UpdateForm, TotalReservationForm

# 테스트중 24.10.28
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# 예약조회 - 검색기능 - 전화번호 조회시 기호제거
from django.db.models import F, Func, Value, CharField
from django.db.models.functions import Replace

from django.http import HttpResponseForbidden


ADMIN_USERS = { "admin" : True,}


def store_list(request):
    return render(request, "manager/manager_index.html")

def production_current_user(request):
    current_user = request.user
    if not current_user.is_authenticated:
        return JsonResponse([], safe=False)

class ManagerStoreList(LoginRequiredMixin, ListView, LoginView, FormView):
    model = rsv.Store
    template_name = "manager/manager_sung_index.html"
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
        context["username"] = current_user.username if current_user.is_authenticated else None
        for admin_user in ADMIN_USERS.keys():
            context["adminusers"] = admin_user

        context['manager'] = self.get_queryset()
        # print(context['manager'])
        manager_list_dicts = [model_to_dict(manager) for manager in self.get_queryset()]
        
        context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)

        if current_user.is_authenticated:
            rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
            messages = models.Message.all_messages(current_user.username)
            context["rsvs"] = rsvs
            context["messages"] = messages
        return context
    
    
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
            print("Reservation_Details 엘스", rsv_model)
            rsv_dict = [model_to_dict(r) for r in rsv_model]
            for r in rsv_dict:
                r.pop("pwhash", None)
                r["rsv_check"] = self.rsv_check(user_id)
            print("엘스", rsv_dict)
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
            # Store의 owner(User 객체)와 연결된 Manager 찾기
            # manager_of_the_store = rsv.Manager.objects.filter(user=store.owner).first()
            # Store의 pk값과 Reservation_user의 store_id값과 일치하는 예약목록 가져오기
            # rsv_objects = rsv.Reservation_user.objects.filter(store_id=store.pk)

            # HttpResponseRedirect를 위한 전달인자
            # pk_value = manager_of_the_store.pk
            # store_id_value = requested_store_id

            # post요청
            if request.method == 'POST':
                 # 전달받은 rsv_ids를 리스트로 변환
                rsv_ids = request.POST.getlist('rsv_ids')
                print("Requested rsv_ids찍어봐라:", rsv_ids)

                # rsv_ids를 정수형으로 변환
                rsv_ids = [int(id) for id in rsv_ids]

                # 해당 ID를 가진 예약 삭제
                rsv.Reservation_user.objects.filter(id__in=rsv_ids, store_id=store.pk).delete()

                # POST 요청 시 입력값을 가져오기
                input1 = request.POST.get('input1', '')
                input2 = request.POST.get('input2', '')
                input3 = request.POST.get('input3', '')

                # 쿼리 매개변수로 입력값을 전달하여 리다이렉트
                return redirect(f"{reverse('input_view')}?input1={input1}&input2={input2}&input3={input3}", pk=store.pk)

                

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

def write(request):
   
    if request.method == 'POST':
        sto = rsv.Store()
        # print(atc.title)
        sto.store_name = request.POST["store_name"]
        sto.address = request.POST["address"]
        sto.owner = request.user
        sto.save()

        
        selectTime = request.POST.getlist("select_time[]")
        sort_value = request.POST.get("sort_set")
        for time in selectTime:
            # print(time)
            sts = rsv.Store_times()
            sts.store_id = sto
            sts.reservation_time = time
            if sort_value == "none":
                print("선택 안 함")
                sts.sort_type = None
            else:
                print("선택함")
                sts.sort_type = sort_value
            print(f"sts.sort_type: {sts.sort_type}")
            sts.save()

    # 폼재전송 방지용 PRG패턴 post -> redirect -> get
        return redirect('write')
    else:
        # GET 요청 처리 (폼을 보여주는 경우)
        return render(request, 'manager/manager_write.html')

    
    # return render(request, 'manager/manager_write.html')


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
class ManagerStoreUpdateView(LoginRequiredMixin, FormView):
    template_name = 'manager/manager_operate.html'
    form_class = ManagerUpdateForm
    store_form_class = StoreUpdateForm

    # 권한설정
    def dispatch(self, request, *args, **kwargs):
        self.manager = get_object_or_404(rsv.Manager, pk=kwargs['pk'])
        self.store = get_object_or_404(rsv.Store, pk=kwargs['store_id'])
        
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

        reservations = rsv.Reservation_user.objects.annotate(
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

        print("전체 콘텍스트 출력: ", context)

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



class Test123(LoginRequiredMixin, UpdateView):
    model = rsv.Store
    form_class = UpdateForm
    template_name = 'manager/manager_update_form.html'

    def get_object(self, queryset=None):
        # self.kwargs에서 'store_id' 값을 가져와서 객체 조회
        store_id = self.kwargs.get('store_id')
        return get_object_or_404(rsv.Store, pk=store_id)
    

# 임시(현재 사용x)
# class Update2(LoginRequiredMixin, UpdateView):
#     model = rsv.Store
#     form_class = UpdateForm
#     template_name = 'manager/manager_update_form.html'

#     def get_object(self, queryset=None):
#         # URL에서 store_id를 사용하여 Store 객체 찾기
#         store_id = self.kwargs.get('store_id')
#         return get_object_or_404(rsv.Store, id=store_id)

#     def dispatch(self, request, *args, **kwargs):
#         self.store = self.get_object()
        
#         # 현재 로그인한 사용자가 Store의 owner와 일치하는지 확인
#         if request.user.is_authenticated and request.user == self.store.owner:
#             return super(Update2, self).dispatch(request, *args, **kwargs)
#         else:
#             raise PermissionDenied

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
        
#         # URL에서 store_id값 가져오기
#         requested_store_id = self.kwargs.get('store_id')
#         context['requested_store_id'] = requested_store_id

#         return context


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
        print("여긴 되냐")
        store_id = self.kwargs.get('store_id')
        self.setup_variables(store_id)
        
        request = self.request
        context = super().get_context_data(**kwargs)

        # URL에서 store_id값 가져오기
        requested_store_id = self.kwargs.get('store_id')
        print("requested_store_id", requested_store_id)
        # print("찍어보자1", requested_store_id)

        # 해당 store_id를 가진 Store 객체 찾기
        # Store테이블의 id값찾기 (url에서 가져온 store_id값과 일치하는)
        # store = get_object_or_404(rsv.Store, pk=requested_store_id)
        store = get_object_or_404(rsv.Store, pk=requested_store_id)
        print("여긴가3")

        if store:
            context['store'] = store
            dates_list = [date.reservation_date for date in self.user_time]
            print("데이트리스트", dates_list)

            # Store의 owner(User 객체)와 연결된 Manager 찾기
            manager_of_the_store = rsv.Manager.objects.filter(user=store.owner).first()
            # print("찍어보자2", manager_of_the_store)
            
            if manager_of_the_store:
                context['manager'] = manager_of_the_store
                print("스토어찍어", store)
                print("스토어네임찍어", store.store_name)

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

            print("찍어보자3", sto_time_objects)
            print("찍어보자3-1", sto_time_objects.values)
            print("찍어보자3-2", wknd_time_objects)
            print("찍어보자3-3", wknd_time_objects.values)
            print("찍어보자3-4", wknd_time_objects)
            print("찍어보자3-5", wknd_time_objects.values)
            
            sto_time_values_list  = {
                'store_id': store.pk,
                'sto_time': list(sto_time_objects.values()),
            }

            print()
            print("찍어보자4 ", sto_time_values_list)
            print("찍어보자4길이 ", len(sto_time_objects))
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
            # context['username'] = request.user.username
            # context['user_dates_json'] = json.dumps(dates_list, cls=DjangoJSONEncoder),

            context["user_dates_json"] = json.dumps(dates_list, cls=DjangoJSONEncoder)
            context["username"] = request.user.username
            print()
            print()
            print("콘텍스트    ", context)

            # context = {
            #     "user_dates_json": json.dumps(dates_list, cls=DjangoJSONEncoder),
            #     "username": request.user.username
            # }
        # print(context['disabled_dates_info_json'])

        # print("콘텍스트", context)
        return context

    # 수정전
    # def post(self, request, *args, **kwargs):

    #     # URL에서 store_id값 가져오기
    #     requested_store_id = self.kwargs.get('store_id')
    #     # Store테이블의 id값을 가진 객체찾기 (url에서 가져온 store_id값과 일치하는)
    #     store = get_object_or_404(rsv.Store, pk=requested_store_id)
    #     if store:
    #         # Store의 owner(User 객체)와 연결된 Manager 찾기
    #         manager_of_the_store = rsv.Manager.objects.filter(user=store.owner).first()
    #         # Store의 pk값과 Store_times의 store_id값과 일치하는 Store_times 가져오기
    #         sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk)
    #         # HttpResponseRedirect를 위한 전달인자
    #         pk_value = manager_of_the_store.pk
    #         store_id_value = requested_store_id

    #         # sto_time_objects의 reservation_time 값들을 리스트로 가져오기
    #         original_time = list(sto_time_objects.values_list('reservation_time', flat=True))

    #         # post요청1
    #         if 'myForm' in request.POST:
    #             button_values_str = request.POST.get('button_values')
    #             added_time = json.loads(button_values_str)
    #             print()
    #             print("button_values_str찍기", button_values_str)
    #             print("added_time찍기", added_time)
    #             print()

    #             # Reservation_user에서 예약 정보 가져오기
    #             reserved_time = []
    #             for sto_time in sto_time_objects:
    #                 reservation_user_objects = rsv.Reservation_user.objects.filter(
    #                     Q(store_id=store) &
    #                     Q(user_time=sto_time.reservation_time)
    #                 )

    #                 # 사용자 예약내역이 존재하면:
    #                 if reservation_user_objects.exists():
    #                     for reservation in reservation_user_objects:

    #                         # user_date_str = reservation.reservation_date
    #                         # print("user_date_str찍어보기", user_date_str)
    #                         datetime_obj = datetime.strptime(reservation.user_time, '%H:%M')
    #                         print("datetime_obj찍어보기", datetime_obj)
    #                         formatted_time_str = datetime_obj.strftime('%H:%M')
    #                         print("formatted_time_str찍어보기", formatted_time_str)
    #                         print("="*30)

    #                         reserved_time.append(formatted_time_str)

    #             # original_time : 사장님이 저장했던 기존시간값
    #             # added_time : 사장님이 변경할 시간 (프론트에서 요청이 들어온)
    #             # reserved_time : 사용자 예약이 존재하는 시간(사용X)
    #             # matching_times_set : 기존시간과 추가된시간의 교집합
    #             # check_added_set : 추가된시간 - 기존시간인 차집합


    #             original_time_set = set(original_time)
    #             added_time_set = set(added_time)
    #             # 교집합
    #             matching_times_set = original_time_set & added_time_set
    #             # 차집합
    #             check_added_set = added_time_set - original_time_set

    #             print("matching_times_set", matching_times_set)
    #             print("matching_times_set갯수", len(matching_times_set))
    #             print("check_added_set갯수", len(check_added_set))
    #             print("="*30)
    #             print()

    #             # 모든 시간이 일치하는 경우
    #             if matching_times_set == original_time_set:
    #                 print("CASE1/ 모든 시간이 존재하거나 처음생성")
    #                 for time in added_time:
    #                     sto_time, created = rsv.Store_times.objects.get_or_create(
    #                         store_id=store,
    #                         reservation_time=time,
    #                     )
    #                     if created:
    #                         print(f"{time}에 대한 새로운 Store_times 객체가 생성되었습니다.")


    #             # 일부 시간이 일치하는 경우
    #             elif len(matching_times_set) > 0:
    #                 print("CASE2/ 일부 시간이 존재")
    #                 # 삭제된 시간은 삭제
    #                 for time in original_time_set - matching_times_set:
    #                     rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
    #                     # rsv.Store_times.save()
    #                     print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

    #                 # 추가된 시간은 추가
    #                 for time in added_time_set - matching_times_set:
    #                     new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
    #                     # rsv.Store_times.save()
    #                     new_store_time.save()
    #                     print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

    #             # 시간이 하나도 일치하지 않는 경우
    #             elif len(matching_times_set) == 0:
    #                 print("CASE3/ 시간이 하나도 일치X")
    #                 print("added_time_set갯수", len(added_time_set))
    #                 print("original_time_set갯수", len(original_time_set))

    #                 # 기존 시간값이 모두 없을경우(삭제 혹은 변경)
    #                 if len(original_time_set) == 0:
    #                     print("3-1/ 기존 시간값이 모두 삭제된경우")

    #                     # original_time 삭제
    #                     for time in original_time_set:
    #                         rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
    #                         print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

    #                     for time in added_time_set:
    #                         new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
    #                         new_store_time.save()
    #                         print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")


    #                 # 기존 시간값이 존재했지만, 삭제되거나 변경되는경우
    #                 elif len(check_added_set) == len(added_time_set):
    #                 # 추가된 시간 - 기존시간을 뺀 값 갯수 = 추가된 시간 갯수 일경우:
    #                     print("3-3/ 기존 시간값이 존재했지만, 삭제되거나 변경되는경우")

    #                     for time in original_time_set:
    #                         rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
    #                         print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")
                        
    #                     for time in added_time_set:
    #                         new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
    #                         new_store_time.save()
    #                         print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

    #                 else: 
    #                     # 오류잡기용
    #                     print("3-4/ 그외")

    #             # POST 처리 완료 시 리디렉션
    #             # return HttpResponseRedirect(reverse('update', kwargs={'pk': pk_value, 'store_id': store_id_value}))
    #             return HttpResponseRedirect(reverse('update3', kwargs={'store_id': store_id_value}))
            
            
    #         # 자바스크립트 post요청 처리
    #         try:
    #             # JSON 데이터 파싱
    #             data = json.loads(request.body)

    #             # 데이터 처리
    #             self.store.start_rsv_possible = data.get("activate_date_start")
    #             self.store.end_rsv_possible = data.get("activate_date_end")
    #             self.store.full_clean()
    #             self.store.save()
                
    #         except json.JSONDecodeError:
    #             return JsonResponse({"message": "유효하지 않은 JSON 형식입니다."}, status=400)
            
        
    #     return self.get(request, *args, **kwargs)
    
    
    # post요청 -> 수정중
    # def post(self, request, *args, **kwargs):

    #     # URL에서 store_id값 가져오기
    #     requested_store_id = self.kwargs.get('store_id')

    #     # Store테이블의 id값을 가진 객체찾기 (url에서 가져온 store_id값과 일치하는)
    #     store = get_object_or_404(rsv.Store, pk=requested_store_id)

    #     if store:
    #         # Store의 owner(User 객체)와 연결된 Manager 찾기
    #         manager_of_the_store = rsv.Manager.objects.filter(user=store.owner).first()


    #         # Store의 pk값과 Store_times의 store_id값과 일치하는 Store_times 가져오기
    #         sto_time_objects = rsv.Store_times.objects.filter(store_id=store.pk)
    #         # print("sto_time_objects", sto_time_objects)
    #         # print("sto_time_objects갯수", len(sto_time_objects))
    #         # print()

    #         # HttpResponseRedirect를 위한 전달인자
    #         pk_value = manager_of_the_store.pk
    #         store_id_value = requested_store_id
            

    #         # sto_time_objects의 reservation_time 값들을 리스트로 가져오기
    #         original_time = list(sto_time_objects.values_list('reservation_time', flat=True))
    #         print("original_time", original_time)
    #         print()

    #         # 이제 모든처리 여기서
    #         try:
    #             # JSON 데이터 파싱
    #             data = json.loads(request.body)
    #             auto_set_req = "activate_date_start" in data or "activate_date_end" in data
    #             manual_set_req = "selected_radio_val" in data or "setting_date" in data
    #             times_set_req = "same" in data or "wd" in data or "wknd" in data

    #             # 갱신주기:수동 (달력)
    #             if auto_set_req: 
    #                 self.store.start_rsv_possible = data.get("activate_date_start")
    #                 self.store.end_rsv_possible = data.get("activate_date_end")
    #                 self.store.renewal_cycle = None
    #                 self.store.base_date = None
    #                 self.store.save()
    #             # 갱신주기:자동
    #             elif manual_set_req:
    #                 self.store.renewal_cycle = data.get('selected_radio_val')
    #                 self.store.base_date = data.get('setting_date')
    #                 self.store.start_rsv_possible = None
    #                 self.store.end_rsv_possible = None
    #                 self.store.save()
    #                 # print("갱신주기", self.store.renewal_cycle)
    #                 # print("기준일", self.store.base_date)
                
    #             # 저장 임시주석
    #             # self.store.full_clean()
    #             # self.store.save()

    #             # 시간값 수정 및 저장
    #             elif times_set_req:

    #                 # mon = data.get('1')
    #                 # print("월찍기", mon)
    #                 # print("셀프찍기", mon.get('times'))
    #                 rsv.Store_times.objects.filter(store_id=store).delete()
    #                 print(f"기존값 삭제 완")

    #                 for key, value_obj in data.items():
    #                     if key != "command":
    #                         sort_type_column_val = key
    #                         times_array = value_obj.get("times", [])
    #                         if times_array:
    #                             for single_time in times_array:
    #                                 rsv.Store_times.objects.create(
    #                                 store_id=store,
    #                                 sort_type=sort_type_column_val,
    #                                 reservation_time=single_time
    #                             )
    #                             # reservation_column_val = times_array
    #                             print(f"{store.pk}/{sort_type_column_val}/{single_time}저장")

    #                             # 기존 sort_type과 현재 요청들어온 sort_type을 비교할 필요없이
    #                             # 그냥 store_id 일치하면 싹 지우고 재생성 하는걸로
    #                     else:
    #                         print("times_array 비어있음")
    #                         pass
    #             return JsonResponse({"status": "success", "message": "성공적으로 변경되었습니다."})
    #         except Exception as e:
    #             print(f"설정 저장중 오류 {e}")
    #             return JsonResponse({"status": "error", "message": f"오류 발생: {e}"}, status=400)


            #     # 이전의 폼으로 제출하던 데이터
            #     button_values_str = data.get('buttonValues')


            #     # button_values_str가 문자열인지 확인
            #     if isinstance(button_values_str, str):
            #         added_time = json.loads(button_values_str)
            #     else:
            #         added_time = button_values_str  # 이미 리스트라면 그대로 사용
                
            #     # added_time = json.loads(button_values_str)
            #     print("button_values_str찍기", button_values_str)
            #     print("added_time찍기", added_time)
            #     # Reservation_user에서 예약 정보 가져오기
            #     reserved_time = []
            #     for sto_time in sto_time_objects:
            #         reservation_user_objects = rsv.Reservation_user.objects.filter(
            #             Q(store_id=store) &
            #             Q(user_time=sto_time.reservation_time)
            #         )

            #         # 사용자 예약내역이 존재하면:
            #         if reservation_user_objects.exists():
            #             for reservation in reservation_user_objects:

            #                 # user_date_str = reservation.reservation_date
            #                 # print("user_date_str찍어보기", user_date_str)
            #                 datetime_obj = datetime.strptime(reservation.user_time, '%H:%M')
            #                 print("datetime_obj찍어보기", datetime_obj)
            #                 formatted_time_str = datetime_obj.strftime('%H:%M')
            #                 print("formatted_time_str찍어보기", formatted_time_str)
            #                 print("="*30)

            #                 reserved_time.append(formatted_time_str)

            #     # original_time : 사장님이 저장했던 기존시간값
            #     # added_time : 사장님이 변경할 시간 (프론트에서 요청이 들어온)
            #     # reserved_time : 사용자 예약이 존재하는 시간(사용X)
            #     # matching_times_set : 기존시간과 추가된시간의 교집합
            #     # check_added_set : 추가된시간 - 기존시간인 차집합


            #     original_time_set = set(original_time)
            #     added_time_set = set(added_time)
            #     # 교집합
            #     matching_times_set = original_time_set & added_time_set
            #     # 차집합
            #     check_added_set = added_time_set - original_time_set

            #     print("matching_times_set", matching_times_set)
            #     print("matching_times_set갯수", len(matching_times_set))
            #     print("check_added_set갯수", len(check_added_set))
            #     print("="*30)
            #     print()

            #     # 모든 시간이 일치하는 경우
            #     if matching_times_set == original_time_set:
            #         print("CASE1/ 모든 시간이 존재하거나 처음생성")
            #         for time in added_time:
            #             sto_time, created = rsv.Store_times.objects.get_or_create(
            #                 store_id=store,
            #                 reservation_time=time,
            #             )
            #             if created:
            #                 print(f"{time}에 대한 새로운 Store_times 객체가 생성되었습니다.")


            #     # 일부 시간이 일치하는 경우
            #     elif len(matching_times_set) > 0:
            #         print("CASE2/ 일부 시간이 존재")
            #         # 삭제된 시간은 삭제
            #         for time in original_time_set - matching_times_set:
            #             rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
            #             # rsv.Store_times.save()
            #             print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

            #         # 추가된 시간은 추가
            #         for time in added_time_set - matching_times_set:
            #             new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
            #             # rsv.Store_times.save()
            #             new_store_time.save()
            #             print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

            #     # 시간이 하나도 일치하지 않는 경우
            #     elif len(matching_times_set) == 0:
            #         print("CASE3/ 시간이 하나도 일치X")
            #         print("added_time_set갯수", len(added_time_set))
            #         print("original_time_set갯수", len(original_time_set))

            #         # 기존 시간값이 모두 없을경우(삭제 혹은 변경)
            #         if len(original_time_set) == 0:
            #             print("3-1/ 기존 시간값이 모두 삭제된경우")

            #             # original_time 삭제
            #             for time in original_time_set:
            #                 rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
            #                 print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")

            #             for time in added_time_set:
            #                 new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
            #                 new_store_time.save()
            #                 print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")


            #         # 기존 시간값이 존재했지만, 삭제되거나 변경되는경우
            #         elif len(check_added_set) == len(added_time_set):
            #         # 추가된 시간 - 기존시간을 뺀 값 갯수 = 추가된 시간 갯수 일경우:
            #             print("3-2/ 기존 시간값이 존재했지만, 삭제되거나 변경되는경우")

            #             for time in original_time_set:
            #                 rsv.Store_times.objects.filter(store_id=store, reservation_time=time).delete()
            #                 print(f"{time} 시간이 rsv.Store_times에서 삭제되었습니다.")
                        
            #             for time in added_time_set:
            #                 new_store_time = rsv.Store_times.objects.create(store_id=store, reservation_time=time)
            #                 new_store_time.save()
            #                 print(f"{time} 시간이 rsv.Store_times에 추가되었습니다.")

            #         else: 
            #             # 오류잡기용
            #             print("3-3/ 그외")
            #             send_data = {
            #                 'message': '올바른 요청이 아닙니다.',
            #                 'status': 'error'
            #             }
                
            #     send_data = {
            #         'message': '변경되었습니다.',
            #         'status': 'success'
            #     }

            #     # POST 처리 완료 시 리디렉션
            #     # return HttpResponseRedirect(reverse('update', kwargs={'pk': pk_value, 'store_id': store_id_value}))
            #     # return HttpResponseRedirect(reverse('update3', kwargs={'store_id': store_id_value}))
            #     return JsonResponse(send_data, safe=False)
            

            # except json.JSONDecodeError:
            #     return JsonResponse({"message": "유효하지 않은 JSON 형식입니다.",'status': 'error'}, status=400)
            
        # return self.get(request, *args, **kwargs)
    

# 비동기 update용 get만드는중 - 근데 일단 UPDATE뷰 post처리부터 끝내고 작업하기
# class UpdateData(View):

#     def setup_variables(self, store_id):
#         # 공통 변수 설정
#         if not hasattr(self, 'store'):
#             self.store = get_object_or_404(rsv.Store, id=store_id)
#         if not hasattr(self, 'store_time'):
#             self.store_time = rsv.Store_times.objects.filter(store_id=store_id)
#         if not hasattr(self, 'user_time'):
#             self.user_time = rsv.Reservation_user.objects.filter(store_id=store_id)
    
#     def get_object(self, queryset=None):
#         # URL에서 store_id를 사용하여 Store 객체 찾기
#         store_id = self.kwargs.get('store_id')
#         return get_object_or_404(rsv.Store, id=store_id)

#     def dispatch(self, request, *args, **kwargs):
#         self.store = self.get_object()
        
#         # 현재 로그인한 사용자가 Store의 owner와 일치하는지 확인
#         if request.user.is_authenticated and request.user == self.store.owner:
#             return super(UpdateData, self).dispatch(request, *args, **kwargs)
#         else:
#             raise PermissionDenied
        

#     def get(self, request, store_id, *args, **kwargs):
#         self.setup_variables(store_id)

#         if not request.user.is_authenticated or request.user.id != self.store.owner_id:
#             return HttpResponseForbidden("접근 권한이 없습니다.")
#         # return JsonResponse(data, safe=False)

#         elif request.user.is_authenticated and request.user.id == self.store.owner_id:
#             # elif 조건수정, 결과 추가하기- try except로 바꾸던가
#             return JsonResponse([], safe=False)

#         else:
#             return JsonResponse([], safe=False)


# @method_decorator(csrf_exempt, name="dispatch")
class NewTest1(View):
    template_name = "manager/test_sung1.html"
    # template_name = "manager/manager_store_detail.html"
    def setup_variables(self, store_id):
        # 공통으로 사용되는 변수들을 설정합니다.
        if not hasattr(self, 'store'):
            self.store = get_object_or_404(rsv.Store, id=store_id)
        if not hasattr(self, 'store_time'):
            self.store_time = rsv.Store_times.objects.filter(store_id=store_id)
        if not hasattr(self, 'user_time'):
            self.user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

    def get(self, request, store_id, *args, **kwargs):
        self.setup_variables(store_id)

        if not request.user.is_authenticated or request.user.id != self.store.owner_id:
            return HttpResponseForbidden("접근 권한이 없습니다.")
        
        dates_list = [date.reservation_date for date in self.user_time]
        print("DT리스트", dates_list)
        
        context = {
            "user_dates_json": json.dumps(dates_list, cls=DjangoJSONEncoder),
            "username": request.user.username
        }

        return render(request, self.template_name, context)
    
    def post(self, request, store_id, *args, **kwargs):
        self.setup_variables(store_id)

        if not request.user.is_authenticated or request.user.id != self.store.owner_id:
            return JsonResponse({"message": "접근 권한이 없습니다."}, status=403)

        try:
            data = json.loads(request.body)
            self.store.start_rsv_possible = data.get("activate_date_start")
            self.store.end_rsv_possible = data.get("activate_date_end")
            self.store.full_clean()
            self.store.save()
        except json.JSONDecodeError:
            return JsonResponse({"message": "유효하지 않은 JSON 형식입니다."}, status=400)
        except ValidationError as e:
            # 유효성 검사 실패 시 에러
            error_message = str(e)
            return HttpResponse(error_message, status=400)


        return JsonResponse({"message": "성공적으로 처리되었습니다."}, status=200)



    
