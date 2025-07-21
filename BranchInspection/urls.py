from django.urls import path
from . import views

app_name = 'BranchInspection'

urlpatterns = [
    path('offsite/', views.offsite_commenting, name='offsite_commenting'),
    path('offsite/submit/', views.submit_offsite_comment, name='submit_offsite_comment'),
    path('offsite/create-submission/', views.create_branch_inspection_submission, name='create_submission'),
    path('manager/submissions/', views.regional_manager_submission_list, name='regional_manager_submission_list'),
    path('manager/submission/<int:branch_id>/set-extension/', views.set_extension, name='set_extension'),
    path('manager/submission/<int:submission_id>/forward/', views.forward_to_monitoring, name='forward_to_monitoring'),
    path('finalize/', views.finalize_submission, name='finalize_submission'),
    path('view/<int:submission_id>/', views.view_submission_detail, name='view_submission_detail'),
    path('dashboard/<int:submission_id>/', views.inspection_dashboard, name='inspection_dashboard'),
    path('submission/<int:submission_id>/return/', views.return_to_branch, name='return_to_branch'),
    path('monitoring-reply/<int:submission_id>/<int:item_id>/', views.monitoring_reply_item, name='monitoring_reply_item'),
    path('submission-overview/', views.submission_overview, name='submission_overview'),
    path('report/monitoring-replies/', views.crm_monitoring_reply_report, name='crm_monitoring_reply_report'),
    path('dgm/finalize-region/', views.finalize_dgm_region, name='finalize_dgm_region'),
    path('dgm/finalize-branch/<int:submission_id>/', views.finalize_branch_monitoring, name='finalize_branch_monitoring'),
    path('undo_finalize_reply/<int:submission_id>/', views.undo_finalize_reply, name='undo_finalize_reply'),
    path('get-region-branch-options/', views.get_region_branch_options, name='get_region_branch_options'),
    path('manage/offsite-items/', views.manage_offsite_items, name='manage_offsite_items'),
    path('manage/offsite-items/add/', views.add_offsite_item, name='add_offsite_item'),
    path('manage/offsite-items/<int:item_id>/edit/', views.edit_offsite_item, name='edit_offsite_item'),
    path('manage/offsite-items/<int:item_id>/delete/', views.delete_offsite_item, name='delete_offsite_item'),

]
