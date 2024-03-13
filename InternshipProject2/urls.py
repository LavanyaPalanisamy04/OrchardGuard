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

from OrchardGuard.views import insert_item_view, load_excel, search, index_documents_opensearch, elastic_search, \

    list_search

    list_search, any_search
origin/search

urlpatterns = [
    path('admin/', admin.site.urls),
    path('insert-item/', insert_item_view, name='insert-item'),
    path('load-data/', load_excel, name='load_excel'),
    path('search/', elastic_search, name='search'),
    path('list-search/', list_search, name='list_search'),

    path('any-search/', any_search, name='any_search'),
 origin/search
    path('index-data/', index_documents_opensearch, name='index-documents'),
]
