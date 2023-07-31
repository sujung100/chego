from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
  path('', views.Idx_list.as_view(), name='Idx_list'),
  path('reserve/', views.reserve, name='reserve'),
  # path('info/', views.info, name='info'),
  path('write/', views.write, name='write'),
]