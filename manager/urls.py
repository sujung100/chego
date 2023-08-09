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

]