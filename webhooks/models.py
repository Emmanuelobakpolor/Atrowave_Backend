from django.db import models

class WebhookLog(models.Model):
    provider = models.CharField(max_length=20)
    reference = models.CharField(max_length=100)
    payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("provider", "reference")

    def __str__(self):
        return f"{self.provider} - {self.reference}"
