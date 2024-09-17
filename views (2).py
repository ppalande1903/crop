from django.shortcuts import render

def home_page(request):
    # return HttpResponse("Hello World! I'm Home.")
    return render(request, 'home.html')
