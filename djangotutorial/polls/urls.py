from django.urls import path

from . import views

app_name = "polls"
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),  # home page
    path('property-calculator/', views.IndexView.as_view(), name='property_calculator'),  # properties calculator
    path('information/', views.InformationView.as_view(), name='information'),  # information page
]
