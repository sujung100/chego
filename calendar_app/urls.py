from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
  path('', views.Idx_list.as_view(), name='Idx_list'),
  path('find_reservation/', views.FindReservationView.as_view(), name='find_reservation'),
  path('input_user_pw/', views.InputUserNameView.as_view(), name='input_user_pw'),

  # 비동기 url
  path('input_user_pw/pass/', views.FetchView.as_view(), name='fetch_view'),
  # path('send_msg/', views.Idx_list.as_view(), name='send_msg'),
  path("api/store_calendar/<int:store_id>/", views.Store_calendar.as_view(), name="store_calendar"),


  
]