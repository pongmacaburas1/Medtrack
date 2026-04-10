# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'
urlpatterns = [
    path("", views.report_center, name="report_center"),
    path("report-center/details/", views.report_details, name="report_details"),
    path("health-conditions/", views.health_conditions_report, name="health_conditions"),
    path("health-monitoring/", views.health_monitoring_dashboard, name="health_monitoring_dashboard"),
    path("medications/fast-moving/", views.fast_moving_medications, name="fast_moving_medications"),
    path("medications/inventory/", views.inventory_report, name="inventory_report"),
]
