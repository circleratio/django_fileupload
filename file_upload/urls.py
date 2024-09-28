from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('new/', views.MultipleFileUploadPage.as_view(), name = 'new'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/<int:file_id>/', views.FileDownload, name='download'),
]

