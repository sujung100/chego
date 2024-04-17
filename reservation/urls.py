from django.urls import path, include
from . import views
from . import sujung_views
# from doit_django.views import UserCreateView, UserCreateDoneTV

urlpatterns = [
  path("",sujung_views.Idx_list.as_view(), name="Idx_list"),
  path('<int:pk>/',views.detail, name='detail'),

  # ajax 
  path("api/store_calendar/<int:store_id>/", sujung_views.Store_calendar.as_view(), name="store_calendar"),
]