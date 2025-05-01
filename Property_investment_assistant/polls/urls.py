from django.urls import path
from .views import IndexView, BoxPlotView, DashboardView
from .views import register_view, login_view, logout_view
from . import views

app_name = "polls"
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),  # home page
    path('property-search/', views.IndexView.as_view(), name='property_calculator'),  # properties calculator
    path('information/', views.InformationView.as_view(), name='information'),  # information page
    path('property-search/boxplot/', BoxPlotView.as_view(), name='boxplot'), # box plot page
    path('bookmark/', views.bookmark_property, name='bookmark_property'),
    path('bookmarks/', views.view_bookmarks, name='view_bookmarks'),
    path('bookmarks/remove/<int:bookmark_id>/', views.remove_bookmark, name='remove_bookmark'),
    path('ml-market-analysis/', views.MLDashboardView.as_view(), name='ml_dashboard'),
    path('market-analysis/', DashboardView.as_view(), name='dashboard'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
