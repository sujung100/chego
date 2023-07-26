from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
  path('', views.list_up, name='list_up'),
  path('reserve/', views.reserve, name='reserve'),
]