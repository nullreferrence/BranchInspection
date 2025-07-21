from django.urls import path
from . import views  # Import your views
from .views import user_login, generate_audit_report, audit_report_page, fetch_notifications, mark_notification_read

app_name = 'audit_workflow'

urlpatterns = [
    path('start_audit/', views.start_audit, name='start_audit'),
    path('submit_objection/<int:audit_id>/<int:item_id>/', views.submit_objection, name='submit_objection'),
    path('audit_summary/<int:audit_id>/', views.audit_summary, name='audit_summary'),
    #path('audit_summary/<int:audit_id>/<int:item_id>/', views.audit_summary, name='audit_summary_item'),
    path('finalize_audit/<int:audit_id>/', views.finalize_audit, name='finalize_audit'),
    path('login/', views.user_login, name='login'),
    path('', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('audit_detail/<int:audit_id>/', views.audit_detail, name='audit_detail'),  # New URL
    path('edit_objection/<int:objection_id>/', views.edit_objection, name='edit_objection'),
    path('audit/<int:audit_id>/comments/<int:item_id>/', views.comment_detail, name='comment_detail'),  # Updated
    path('logout/', views.user_logout, name='user_logout'),
    path('password_change/', views.change_password, name='change_password'),
    #path('objection_file_upload/<int:objection_id>/', views.objection_file_upload, name='objection_file_upload'),
    path('generate-audit-report/<int:audit_id>/', generate_audit_report, name='generate_audit_report'),
    path('audit-report/<int:audit_id>/', audit_report_page, name='audit_report_page'),
    path('items/', views.item_list, name='item_list'),
    path('item/add/', views.add_or_update_item, name='add_item'),
    path('item/update/<int:item_id>/', views.add_or_update_item, name='update_item'),
    path('item/delete/<int:item_id>/', views.delete_item, name='delete_item'),
    path('admin_objection_decision/<int:audit_objection_id>/', views.admin_objection_decision, name='admin_objection_decision'),
    path('jaripotro/<int:audit_id>/', views.jaripotro_report, name='jaripotro_report'),
    path('jaripotro/download/<int:audit_id>/', views.download_jaripotro_docx, name='download_jaripotro_docx'),
    path('authorize/<int:audit_id>/', views.authorize_submission, name='authorize_submission'),
    path("notifications/fetch/", fetch_notifications, name="fetch_notifications"),
    path("notifications/mark-read/<int:notification_id>/", mark_notification_read, name="mark_notification_read"),

]
