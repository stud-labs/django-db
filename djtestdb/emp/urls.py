from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="dep_index"),
    path("department/<str:number>/", views.emp_index, name="emp_index"),
    path("employee/<int:tablenumber>/", views.emp_view, name="emp_view"),
    path("employee/<int:tablenumber>/store/", views.emp_store, name="emp_store"),
]
