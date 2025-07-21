"""bangaidj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf import settings
from django.views.static import serve
from django.urls import path
from .views import menu_page
#from cost_management.views import GeneratePdf

urlpatterns = [
    path('admin/', admin.site.urls),
    path('main/', include('main.urls')),
    path('', include('audit_workflow.urls', namespace='audit_workflow')),
    path('BranchInspection/', include('BranchInspection.urls', namespace='BranchInspection')),
    # path('idea', include('blog_post.urls'), name='idea'),
    # path('audit/', include('audit_management.urls'), name='audit'),
    # path('creditReport/', include('creditReport.urls'), name='creditReport'),
    # path('commodity/', include('commodityprice.urls'), name='commodity'),
    # path('lc/', include('lc.urls'), name='lc'),
    #path('internal/', include('internal_audit.urls'), name='internal'),


     #path('FeCircular/', include('FeCircular.urls'), name='FeCircular'),
    # path('dataapp/', include('dataapp.urls'), name = 'dataapp'),
    # path('api_comparison/', include('api_comparison.urls'), name = 'api_comparison'),
    # path('exchange_comparison/', include('exchange_comparison.urls'), name = 'exchange_comparison'),
    # path('', menu_page, name='menu'),

    path('budget/', include('budget_register.urls')),
  
]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, serve, document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)





if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
