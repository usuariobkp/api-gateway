from django.db import models
from django.utils.translation import gettext_lazy as _


class Query(models.Model):
    """Registro de queries exitosas, guardadas con el propósito de analytics"""
    ip_address = models.CharField(max_length=200, null=True)
    host = models.TextField()
    uri = models.TextField()
    querystring = models.TextField()
    start_time = models.DateTimeField()
    request_time = models.DurationField()

    class Meta:
        verbose_name = _("query")
        verbose_name_plural = _("queries")

    def __str__(self):
        return 'Query at %s: %s' % (self.start_time, self.uri)
