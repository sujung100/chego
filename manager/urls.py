from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from . import sungwoo_views

urlpatterns = [
  # 안쓰는것들
  # path("",views.store_list, name="index"),
  # path('logout/', auth_views.LogoutView.as_view(next_page="index"), name='logout'),
  # path("",views.write, name="write"),
  # path('<int:pk>/',views.detail, name='detail'),
  # path("<str:template_choice>/", views.ManagerStoreList.as_view(), name="operate"),
  # path("operate/", views.operate, name="operate"),
  # path('operate/<int:pk>/', views.ManagerUpdateList.as_view(), name='mng_update'),
  # path('search/', views. search, name='search'),



  path("",views.ManagerStoreList.as_view(), name="index"),
  path("write/",views.write, name="write"),
  path("login/",views.UserLoginView.as_view(),name="login"),
  path("signup/",views.UserSignUpView.as_view(),name="signup"),
  path("signup/done",views.UserCreateDoneTV.as_view(),name="signup_done"),


  path('operate/<int:pk>_<int:store_id>/', views.ManagerStoreUpdateView.as_view(), name='mng_update'),
  path('update/<int:pk>_<int:store_id>/', views.Update.as_view(), name='update'),

  path('sung/operate/<int:pk>_<int:store_id>/', sungwoo_views.ManagerStoreUpdateView.as_view(), name='mng_update'),
  # path('sung/update/<int:pk>_<int:store_id>/', sungwoo_views.Update.as_view(), name='update'),
  # pk값 하나떼버림..임시
  path('sung/update/<int:store_id>/', sungwoo_views.Update2.as_view(), name='update'),

# 성우님
  path("sung/",sungwoo_views.ManagerStoreList.as_view(), name="sungwoo"),
  path("sung/admin_chat2/", sungwoo_views.AdminChat2.as_view(), name="admin_chat2"),
  # 변경전 - pk로 store_id값만 가져와야함.. 변경전 operate에서는 <int:pk>_<int:store_id>두개 가져왔지만
  # 기존
  # path('sung/<int:store_id>/', sungwoo_views.detail_list, name='store_detail'),
  # 변경
  path('sung/<int:store_id>/', sungwoo_views.Total_Reservation_Check.as_view(), name='store_detail'),


# 비동기
  path("sung/api/store-times/", sungwoo_views.StoreTimesView.as_view(), name='store_times'),
  # fetch말고 웹소켓으로 예약정보 가져옴 -이제필요없음
  # path('sung/api/schedules/<int:pk>/', sungwoo_views.Schedules.as_view(), name='schedules'),
  path("sung/api/reservation_false/", sungwoo_views.Reservation_Details.as_view(), name="reservation_details"),
  path("sung/api/reservation_id/<int:id>/", sungwoo_views.Reservation_Details.as_view(), name="reservation_id"),
  path("sung/admin_chat2/api/chat-room/user_info/", sungwoo_views.UserInfo.as_view(), name="user_info"),
  path("sung/admin_chat2/api/chat-room/", sungwoo_views.ChatRoom.as_view(), name="chat_room2"),
  path("sung/admin_chat2/api/chat-room/<str:chatroom_name>/messages/", sungwoo_views.EnterChatRoom.as_view(), name="enter_chatroom2"),

]