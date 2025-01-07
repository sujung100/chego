from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
    # 변경

  path('', views.Idx_list.as_view(), name='Idx_list'),

  path('find_reservation/', views.FindReservationView.as_view(), name='find_reservation'),
  path('input_user_pw/', views.InputUserNameView.as_view(), name='input_user_pw'),

  # 비동기 url 생성
  path('input_user_pw/pass/', views.FetchView.as_view(), name='fetch_view'),


]