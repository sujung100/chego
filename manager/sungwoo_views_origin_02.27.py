from django.shortcuts import render, redirect, get_object_or_404
from calendar_app import models as rsv

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

from django.http import JsonResponse, QueryDict, HttpRequest
from django.views import View
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from . import models


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
    def get(self, request, id=None):
        production_current_user(request)
        if id:
            rsv_model = get_object_or_404(rsv.Reservation_user.objects.defer("pwhash"), id=id)
            rsv_dict = model_to_dict(rsv_model)
            rsv_dict.pop("pwhash", None)
        else:
            user_id = request.user.id
            print(user_id)
            rsv_model = rsv.Reservation_user.objects.defer("pwhash").filter(store_id__owner_id=user_id, reservation_check=False)
            print("Reservation_Details 엘스", rsv_model)
            rsv_dict = [model_to_dict(r) for r in rsv_model]
            for r in rsv_dict:
                r.pop("pwhash", None)
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
    
     

