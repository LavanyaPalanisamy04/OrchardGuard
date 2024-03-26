"""
URL configuration for InternshipProject2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path

from OrchardGuard.views import index_documents_opensearch, elastic_search, \
    list_search, any_search, export_csv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('search/', elastic_search, name='search'),
    path('list-search/', list_search, name='list_search'),
    path('any-search/', any_search, name='any_search'),
    path('index-data/', index_documents_opensearch, name='index-documents'),
    path('export-csv/', export_csv, name='export_csv')
]
