from django.shortcuts import render

# Create your views here.

def list_up(request):
    return render(request, "main1.html")

def reserve(request):
    return render(request, "main2.html")