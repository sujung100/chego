from django.shortcuts import render

# Create your views here.

def list_up(request):
    return render(request, "listup.html")

def reserve(request):
    return render(request, "reservation.html")