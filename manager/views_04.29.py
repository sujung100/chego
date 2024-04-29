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
from django.core import serializers

from django.http import JsonResponse, QueryDict, HttpRequest
from django.views import View
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from . import models
from django.db.models import Q, Value, CharField
from django.db.models.functions import Replace
from datetime import datetime
from django.views import View
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


ADMIN_USERS = { "admin" : True,}

# Create your views here.
def store_list(request):
    return render(request, "manager/manager_index.html")

def production_current_user(request):
    current_user = request.user
    if not current_user.is_authenticated:
        return JsonResponse([], safe=False)

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
        context["username"] = current_user.username if current_user.is_authenticated else None
        for admin_user in ADMIN_USERS.keys():
            context["adminusers"] = admin_user

        context['manager'] = self.get_queryset()
        # print(context['manager'])
         # QuerySet to list of dicts.
        manager_list_dicts = [model_to_dict(manager) for manager in self.get_queryset()]
        
        # List of dicts to JSON string.
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


# class ChatRoom(View):
#     def get(self, request, chatroom, *args, **kwargs):
#         try:
#             messages = Message.all_messages(chatroom)
#             result = []
#             for message in messages:
#                 result.append({
#                     'id': str(message.id),
#                     'author': message.author.username,
#                     'recipient': message.recipient.username,
#                     'content': message.content,
#                     'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M"),
#                 })
#             return JsonResponse(result, safe=False)
#         except Message.DoesNotExist:
#             return JsonResponse({'error': 'Chatroom not found'}, status=404)

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

    
    # def get_context_data(self, **kwargs):
    #     context = {}
    #     current_user = self.request.user
    #     context["username"] = current_user.username if current_user.is_authenticated else None
    #     # for admin_user in ADMIN_USERS.keys():
    #     #     context["adminusers"] = admin_user

    #     context["adminusers"] = list(ADMIN_USERS.keys())

    #     context['manager'] = self.get_queryset()

    #     # QuerySet to list of dicts.
    #     manager_list_dicts = [model_to_dict(manager) for manager in context['manager']]
        
    #     # List of dicts to JSON string.
    #     context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)
    #     if current_user.is_authenticated:
    #         rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
    #         messages = self.get_messages(current_user.username)
    #         context["rsvs"] = rsvs
    #         context["messages"] = messages
    #     return JsonResponse(context, safe=False)

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

class DetailListView2(View):
    template_name = "manager/manager_store_detail.html"

    def get(self, request, store_id, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        store_id = self.kwargs['store_id']
        store = get_object_or_404(rsv.Store, id=store_id)
        manager = rsv.Manager.objects.get(user=self.request.user)

        context = {}
        context['manager'] = manager
        context['store'] = store

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
            store_id=store
        ).distinct()

        paginator = Paginator(reservations, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['kw'] = kw

        store_time = rsv.Store_times.objects.filter(store_id=store_id)
        user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

        user_dates = []
        dates_list = [date.reservation_date for date in user_time]
        user_dates.append({
            "user_dates" : dates_list
        })
        context["user_dates_json"] = json.dumps(dates_list, cls=DjangoJSONEncoder)
        context["username"] = self.request.user.username if self.request.user.is_authenticated else None

        return context

class IntegratedDetailView(View):
    template_name = "manager/manager_store_detail.html"
    
    def setup_variables(self, request, store_id):
        try:
            self.store = get_object_or_404(rsv.Store, id=store_id)
            self.store_time = rsv.Store_times.objects.filter(store_id=store_id)
            self.user_time = rsv.Reservation_user.objects.filter(store_id=store_id)
            self.manager = rsv.Manager.objects.get(user=request.user) if request.user.is_authenticated else None
        except rsv.Manager.DoesNotExist:
            # Manager 객체가 존재하지 않는 경우의 처리
            # 예: 새 Manager 객체 생성 또는 사용자에게 오류 메시지 반환
            return HttpResponse('Manager 객체가 존재하지 않습니다.', status=404)
    def get(self, request, store_id, *args, **kwargs):
        self.setup_variables(request, store_id)
        context = self.get_context_data(store_id=store_id, **kwargs)
        # template_name = self.get_template_name(request)
        return render(request, self.template_name, context)
    
    def post(self, request, store_id, *args, **kwargs):
        self.setup_variables(store_id)
        if not request.user.is_authenticated or request.user.id != self.store.owner_id:
            return JsonResponse({"message": "접근 권한이 없습니다."}, status=403)
        # POST 요청 처리 로직 (DetailListView의 POST 처리 로직을 여기에 포함시킵니다.)
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
    
    def get_context_data(self, **kwargs):
        store_id = self.kwargs['store_id']
        store = get_object_or_404(rsv.Store, id=store_id)
        try:
            manager = rsv.Manager.objects.get(user=self.request.user)
        except rsv.Manager.DoesNotExist:
            manager = None    
        context = {}
        # DetailListView2의 get_context_data 로직을 여기에 통합합니다.
        # 필요한 경우, DetailListView의 로직도 여기에 포함시킬 수 있습니다.
        context['manager'] = manager
        context['store'] = store

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
            store_id=store
        ).distinct()

        paginator = Paginator(reservations, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj
        context['kw'] = kw

        store_time = rsv.Store_times.objects.filter(store_id=store_id)
        user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

        user_dates = []
        dates_list = [date.reservation_date for date in user_time]
        user_dates.append({
            "user_dates" : dates_list
        })
        context["user_dates_json"] = json.dumps(dates_list, cls=DjangoJSONEncoder)
        context["username"] = self.request.user.username if self.request.user.is_authenticated else None
        return context
        
@method_decorator(csrf_exempt, name="dispatch")
class DetailListView(View):
    template_name = "manager/manager_store_detailcopy0306.html"
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

# @method_decorator(csrf_exempt, name="dispatch")
# class DetailListView(View):
#     template_name = "manager/manager_store_detailcopy0306.html"

#     def get(self, request, store_id, *args, **kwargs):
#         store = get_object_or_404(rsv.Store, id=store_id)
#         store_time = rsv.Store_times.objects.filter(store_id=store_id)
#         user_time = rsv.Reservation_user.objects.filter(store_id=store_id)

#         if request.user.id != store.owner_id:
#             return HttpResponseForbidden("접근 권한이 없습니다.")
            
#         user_dates = []
#         dates_list = [date.reservation_date for date in user_time]
#         # print(dates_list)
#         user_dates.append({
#             "user_dates" : dates_list
#         })
#         context = {"user_dates_json" : json.dumps(dates_list, cls=DjangoJSONEncoder)}
#         current_user = request.user
#         context["username"] = current_user.username if current_user.is_authenticated else None

#         return render(request, self.template_name, context)
        
#     def post(self, request, store_id, *args, **kwargs):
#         data = json.loads(request.body)
#         start_date = data.get('activate_date_start')
#         end_date = data.get('activate_date_end')
        
#         # 데이터 처리 로직 (예시)
#         # 예를 들어, 받은 날짜로 무언가를 활성화하는 로직을 추가할 수 있습니다.
        
#         # 처리 후 클라이언트에 응답 반환
#         return JsonResponse({"message": "성공적으로 처리되었습니다."}, status=200)

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
    # return render(request, "manager/test/test_chat_copy.html")

@login_required
def test_room(request, room_name):
    context = {
        "room_name_json" : mark_safe(json.dumps(room_name)),
        "username" : request.user.username,
    }
    return render(request, "manager/test/test_room.html", context)
    # return render(request, "manager/test/test_room22.html", context)

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

        # QuerySet to list of dicts.
        manager_list_dicts = [model_to_dict(manager) for manager in context['manager']]
        
        # List of dicts to JSON string.
        context['store_json'] = json.dumps(manager_list_dicts, cls=DjangoJSONEncoder)
        if current_user.is_authenticated:
            rsvs = rsv.Reservation_user.objects.all().order_by("-reservation_date")
            messages = self.get_messages(current_user.username)
            context["rsvs"] = rsvs
            context["messages"] = messages
        return context
    
     

