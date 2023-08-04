from django.urls import path
from . import views

urlpatterns = [
  path("",views.store_list, name="index"),
  path("write/",views.write, name="write"),
  path("login/",views.UserLoginView.as_view(),name="login"),
  path("signup/",views.UserSignUpView.as_view(),name="signup"),
  # path("",views.write, name="write"),
  # path('<int:pk>/',views.detail, name='detail'),
]