from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('houses/', views.list_houses, name='list_houses'),
    path('show-data/', views.show_data, name='show_data'),
]
