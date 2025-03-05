from django.urls import path
from .views import IndexView, BoxPlotView 
from . import views

app_name = "polls"
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),  # home page
    path('property-calculator/', views.IndexView.as_view(), name='property_calculator'),  # properties calculator
    path('information/', views.InformationView.as_view(), name='information'),  # information page
    path('property-calculator/boxplot/', BoxPlotView.as_view(), name='boxplot'), # box plot page
    path('bookmark/', views.bookmark_property, name='bookmark_property'),
    path('bookmarks/', views.view_bookmarks, name='view_bookmarks'),
    path('bookmarks/remove/<int:bookmark_id>/', views.remove_bookmark, name='remove_bookmark'),
]
