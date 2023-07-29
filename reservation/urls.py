from django.urls import path, include
from . import views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
  path("",views.write, name="write"),
  path('<int:pk>/',views.detail, name='detail'),
]