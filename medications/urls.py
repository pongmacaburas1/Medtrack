from django.urls import path
from . import views

app_name = 'medications'

urlpatterns = [
    # Prescription list
    path('list/', views.medication_list, name='medication_list'),
    
    # Medication inventory
    path('inventory/', views.medication_inventory_list, name='inventory_list'),
    path('inventory/add/', views.medication_add, name='medication_add'),
    path('inventory/<int:pk>/', views.medication_detail, name='medication_detail'),
    path('inventory/<int:pk>/update/', views.medication_update_inventory, name='update_inventory'),
    path('inventory/<int:pk>/history/', views.medication_history, name='medication_history'),
    path('inventory/<int:pk>/edit/', views.medication_edit, name='medication_edit'),
    path('inventory/<int:pk>/delete/', views.medication_delete, name='medication_delete'),
    
    # Prescription management
    path('prescription/create/', views.prescription_create, name='prescription_create'),
    # Stub detail view route; implement later if you don’t have it yet:
    path("prescriptions/details/r<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("prescriptions/<int:pk>/print/", views.prescription_printable, name="prescription_printable"),
    path("prescription/<int:pk>/delete/", views.prescription_delete, name="prescription_delete"),
    path('prescription/<int:pk>/update/', views.prescription_update, name='prescription_update'),
]