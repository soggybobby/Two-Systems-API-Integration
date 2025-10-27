# sales_site/sales_site/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("sales.urls")),   # include everything once
]
