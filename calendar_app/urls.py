from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
    # 변경

  path('', views.Idx_list.as_view(), name='Idx_list'),
  # path('reservation/', views.FindReservationView.as_view(), name='Reserve_list'),

  # path('reservation/', views.FindReservationView.as_view(), name='Reserve_list'),
  # path('reservation_detail/<int:reservation_id>/', views.DetailView.as_view(), name='Detail_view'),


  path('find_reservation/', views.FindReservationView.as_view(), name='find_reservation'),
  path('input_user_pw/', views.InputUserNameView.as_view(), name='input_user_pw'),
  path('detail_view/', views.DetailView.as_view(), name='detail_view'),
  path('delete_fin/', views.ReservationDeletedView.as_view(), name='reservation_deleted_view'),


  path('first/', views.First_list.as_view(), name='First_list'),
  path('reserve/', views.reserve, name='reserve'),
  # path('info/', views.info, name='info'),
  path('write/', views.write, name='write'),
  path('test/', views.Test_list.as_view(), name='Test_list'),
]