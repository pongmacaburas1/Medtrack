from django.urls import path

"""
URL configuration for the consultations app.

This module defines the URL patterns for the consultations app, mapping
specific URL paths to their corresponding view functions. These URLs handle
various functionalities such as viewing the doctor dashboard, managing
consultation schedules, and handling consultation cancellations and rescheduling.

Routes:
- doctor-dashboard: Displays the doctor's dashboard.
- calendar/: Displays all consultations in a calendar view.
- calendar-physician/<int:physician_id>/: Displays consultations filtered by a specific physician.
- schedule/: Allows scheduling a new consultation.
- cancel/<int:consultation_id>/: Cancels a specific consultation.
- reschedule/<int:consultation_id>/: Reschedules a specific consultation.

Namespace:
- app_name: 'consultations' (used for namespacing URLs in templates and reverse lookups).
"""

from . import views

app_name = 'consultations'

urlpatterns = [
    path("new/", views.ConsultationCreateView.as_view(), name="consultation_create"),
    path("history/", views.consultation_history, name="consultation_history"),

    path('doctor-dashboard', views.doctor_dashboard, name='doctor_dashboard'),
    path('calendar/', views.all_consultations, name='consultation_calendar'),
    path('calendar-physician/<int:physician_id>/', views.consultations_by_physician, name='consultation_calendar_physician'),
    path('schedule/', views.schedule_consultation, name='schedule_consultation'),
    path('cancel/<int:consultation_id>/', views.cancel_consultation, name='cancel_consultation'),
    path('reschedule/<int:consultation_id>/', views.reschedule_consultation, name='reschedule_consultation'),
     path('complete/<int:consultation_id>/', views.complete_consultation, name='complete_consultation'),
    path("<int:pk>/print/", views.consultation_printable, name="consultation_printable"),
    path('create/', views.create_consultation, name='create_consultation'),
    path('api/pdls/', views.pdl_list_api, name='pdl_list_api'),
    path('api/physicians/', views.physician_list_api, name='physician_list_api'),
    path('api/consultation-reasons/', views.consultation_reason_list_api, name='consultation_reason_list_api'),
    path('api/locations/', views.location_list_api, name='location_list_api'),
    path('api/consultation-time-blocks/', views.consultation_time_block_list_api, name='consultation_time_block_list_api'),
]