from django.urls import path

from . import views

urlpatterns = [
    #path('administrator', views.admin_level_template_view, name='admin_level_template_list'),
    #path('instructor', views.instructor_level_template_view, name='policy_template_list'),
    path('', views.process_lti_launch_request_view, name='process_lti_launch_request'),
    path('policy_templates_list/', views.policy_templates_list_view, name='policy_templates_list'),
    path('student_published_policy/', views.student_published_policy_view, name='student_published_policy'),
    path('template/<int:pk>/edit/', views.AdminLevelTemplateUpdateView.as_view(), name='admin_level_template_edit'),
    path('policy/<int:pk>/edit/', views.instructor_level_policy_edit_view, name='instructor_level_policy_edit'),
    path('published_policy/<int:pk>/', views.instructor_published_policy, name='instructor_published_policy'),
    path('edit_published_policy/<int:pk>/', views.edit_published_policy, name='edit_published_policy'),
    path('instructor_delete_old_publish_new/<int:pk>/', views.instructor_delete_old_publish_new_view, name='instructor_delete_old_publish_new'),
]
