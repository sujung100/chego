from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
    # 변경

  path('', views.Idx_list.as_view(), name='Idx_list'),
  path('reservation/', views.FindReservationView.as_view(), name='Reserve_list'),


  path('first/', views.First_list.as_view(), name='First_list'),
  path('reserve/', views.reserve, name='reserve'),
  # path('info/', views.info, name='info'),
  path('write/', views.write, name='write'),
  path('test/', views.Test_list.as_view(), name='Test_list'),
]