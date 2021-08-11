from os import name
from django.urls import include, path
from rest_framework import routers
from . import views
#from django.contrib import admin


router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls)),
    path('clinical-api', views.ClinicalAPI.as_view(), name='clinical-api'),
    path('clinical-user', views.ClinicalUser.as_view(), name='clinical-user'),
    path('user-favourites', views.UserFavourites.as_view(), name='user-favourites'),
    path('add-favourites', views.AddFavourites.as_view(), name='add-favourites'),
    path('user-history', views.ViewHistory.as_view(), name='user-history')
]
