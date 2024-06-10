from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from extractor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.upload_file, name='upload_file'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
