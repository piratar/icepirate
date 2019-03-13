from django.shortcuts import render

def management(request):
    ctx = {
    }
    return render('core/management.html', ctx)

