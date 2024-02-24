from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
  # path("",views.store_list, name="index"),
  path("",views.ManagerStoreList.as_view(), name="index"),
  path("write/",views.write, name="write"),
  path("login/",views.UserLoginView.as_view(),name="login"),
  # path('logout/', auth_views.LogoutView.as_view(next_page="index"), name='logout'),
  path("signup/",views.UserSignUpView.as_view(),name="signup"),
  path("signup/done",views.UserCreateDoneTV.as_view(),name="signup_done"),
  # path("",views.write, name="write"),
  # path('<int:pk>/',views.detail, name='detail'),
  path('<int:store_id>/', views.detail_list, name='store_detail'),

  # chat 테스트
  path("testchat/", views.test_chat, name="test_chat"),
  path("testchat/<str:room_name>/", views.test_room, name="test_room"),
  path("customer_service_center/inquiry/", views.admin_chat, name="admin_chat"),
  # path("admin_chat2/", views.admin_chat2, name="admin_chat2"),
  path("admin_chat2/", views.AdminChat2.as_view(), name="admin_chat2"),

  # ajax
  path('api/store-times/', views.StoreTimesView.as_view(), name='store_times'),
  path("customer_service_center/inquiry/api/chat-room/", views.ChatRoom.as_view(), name="chat_room"),
  path("admin_chat2/api/chat-room/", views.ChatRoom.as_view(), name="chat_room2"),
  path('customer_service_center/inquiry/api/chat-room/<str:chatroom_name>/', views.EnterChatRoom.as_view(), name='enter_chatroom'),
  # path("admin_chat2/api/chat-room/<str:chatroom_name>/", views.EnterChatRoom.as_view(), name="enter_chatroom2"),
  path("admin_chat2/api/chat-room/<str:chatroom_name>/messages/", views.EnterChatRoom.as_view(), name="enter_chatroom2"),
  # path("admin_chat2/api/chat-room/<int:page_number>/", views.EnterChatRoom.as_view(), name="enter_chatroom2"),
  path("admin_chat2/api/chat-room/user_info/", views.UserInfo.as_view(), name="user_info"),
  path("api/reservation_id/<int:id>/", views.Reservation_Details.as_view(), name="reservation_id"),
  path("api/reservation_false/", views.Reservation_Details.as_view(), name="reservation_details"),
]