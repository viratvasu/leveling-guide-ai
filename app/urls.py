from django.urls import path
from . import views

urlpatterns = [
    # Health check for ECS/load balancer
    path('api/health/', views.health_check, name='health_check'),
    
    # Auth
    path('api/auth/login/', views.login, name='login'),
    
    # Levelling Guide
    path('api/guides/upload/', views.upload_guide, name='upload_guide'),
    path('api/guides/<int:guide_id>/generate/', views.generate_guide_examples, name='generate_guide'),
    path('api/guides/<int:guide_id>/regenerate-cell/', views.regenerate_cell, name='regenerate_cell'),
    path('api/guides/<int:guide_id>/regenerate-all/', views.regenerate_all, name='regenerate_all'),
    path('api/guides/<int:guide_id>/set-current/', views.set_current_version, name='set_current_version'),
    path('api/guides/', views.list_guides, name='list_guides'),
    path('api/guides/current/', views.get_current_guide, name='get_current_guide'),
    path('api/guides/<int:guide_id>/', views.get_guide, name='get_guide'),
]

