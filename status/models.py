from django.db import models


class RVM(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, default="Cairo")
    is_active = models.BooleanField(default=True)
    last_usage = models.DateTimeField(
        null=True, blank=True, default=None
    )  # updated each time machine used (future task)

    class Meta:
        ordering = ("-last_usage",)

    def __str__(self):
        return f"{self.name} ({self.location})"
