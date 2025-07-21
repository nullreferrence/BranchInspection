# views.py
from django.shortcuts import render

def menu_page(request):
    services = [
        {"name": "Admin", "url": "/admin/"},
        {"name": "Idea", "url": "/idea"},
        {"name": "Audit", "url": "/audit/"},
        {"name": "Credit Report", "url": "/creditReport/"},
        {"name": "Commodity", "url": "/commodity/"},
        {"name": "LC", "url": "/lc/"},
        {"name": "Fe Circular", "url": "/FeCircular/"},
    ]
    return render(request, 'menu.html', {"services": services})
