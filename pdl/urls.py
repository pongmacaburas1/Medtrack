from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'pdl'

urlpatterns = [
    path('', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='pdl:login'), name='logout'),
    path('list/', views.pdl_list, name='pdl_list'),
    path('profile/<str:username>/', views.pdl_profile, name='pdl_profile'),
    path('add/', views.add_pdl, name='add_pdl'),
    path("api/pdl/<int:pk>/latest-room/", views.pdl_detention_room_api, name="pdl_latest_room_api"),
    path("edit/<int:pdl_id>/", views.edit_pdl, name="edit_pdl"),
    path("p/<int:pk>/delete/", views.delete_pdl, name="delete_pdl"),

    # Health Conditions
    path("profile/<int:pdl_id>/health/add/", views.health_condition_add, name="health_condition_add"),
    path("health/<int:pk>/edit/", views.health_condition_edit, name="health_condition_edit"),
    path("health/<int:pk>/delete/", views.health_condition_delete, name="health_condition_delete"),

    # IT Admin Panel
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-panel/users/create/", views.admin_create_user, name="admin_create_user"),
    path("admin-panel/users/<int:pk>/role/", views.admin_edit_role, name="admin_edit_role"),
    path("admin-panel/users/<int:pk>/delete/", views.admin_delete_user, name="admin_delete_user"),
    path("admin-panel/users/<int:pk>/reset-password/", views.admin_reset_password, name="admin_reset_password"),
    path("admin-panel/users/<int:pk>/history/", views.admin_user_history, name="admin_user_history"),
]