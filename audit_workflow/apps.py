from django.apps import AppConfig

class AuditWorkflowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit_workflow'

    def ready(self):
        import audit_workflow.signals  # existing
        import audit_workflow.models  # ✅ new — ensures models are registered
