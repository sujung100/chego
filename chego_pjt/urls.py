from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    # path("",views.Idx.as_view(),name="index"),

    # path("", views.Idx, name="index"),
    # path("", views.Idx_list.as_view(), name="index"),
    path("", views.Idx_list.as_view(), name="main4"),
    # path("", views.Idx_list.as_view(), name="list_up"),
    path('admin/', admin.site.urls),
    path('reservation/', include('reservation.urls')),
    path('manager/', include('manager.urls')),
    path('manager/',include('django.contrib.auth.urls')),

    # REST 프레임워크
    path("api-auth/", include("rest_framework.urls")),
]
