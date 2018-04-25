import urllib.parse

from abc import abstractmethod

import requests

from django.conf import settings
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse

from api_management.apps.api_registry.validators import HostsValidator, \
    UrisValidator, \
    AlphanumericValidator
from api_management.apps.api_registry.signals import token_request_accepted
from api_management.apps.api_registry.helpers import kong_client_using_settings


API_GATEWAY_LOG_PLUGIN_NAME = 'api-gateway-httplog'


class KongObject(models.Model):

    enabled = models.BooleanField(default=False)
    kong_id = models.UUIDField(null=True)

    class Meta:
        abstract = True

    def is_enabled(self):
        return self.enabled

    def get_kong_id(self):
        return str(self.kong_id)

    def manage_kong(self, kong_client):
        if self.is_enabled():
            self.update_or_create_kong(kong_client)

        elif self.kong_id:
            self.delete_kong(kong_client)

    def update_or_create_kong(self, kong_client):
        if self.kong_id:
            response = self.update_kong(kong_client)
        else:
            response = self.create_kong(kong_client)
        self.kong_id = response['id']

    @abstractmethod
    def create_kong(self, kong_client):
        pass

    @abstractmethod
    def update_kong(self, kong_client):
        pass

    @abstractmethod
    def delete_kong(self, kong_client):
        pass


class KongApi(KongObject):

    name = models.CharField(unique=True, max_length=200, validators=[AlphanumericValidator()])
    upstream_url = models.URLField()
    hosts = models.CharField(max_length=200, validators=[HostsValidator()], blank=True, default='')
    uri = models.CharField(max_length=200, validators=[UrisValidator()], blank=True, default='')
    strip_uri = models.BooleanField(default=True)
    preserve_host = models.BooleanField(default=False)
    documentation_url = models.URLField(blank=True)
    docs_kong_id = models.UUIDField(null=True)  # TODO: Refactor, split responsability

    def __str__(self):
        return self.name

    def clean(self):
        if not (self.uri or self.hosts):
            raise ValidationError("At least one of 'hosts' or 'uris' must be specified")

        return super(KongApi, self).clean()

    def create_kong(self, kong_client):
        self._create_docs_api(kong_client)
        return self._create_main_api(kong_client)

    def _create_main_api(self, kong_client):
        response = kong_client \
            .apis.create(self.name,
                         upstream_url=self.upstream_url,
                         hosts=self.hosts,
                         uris=self._api_uri_pattern(),
                         strip_uri=self.strip_uri,
                         preserve_host=self.preserve_host)
        self.kong_id = response['id']
        return response

    def _api_uri_pattern(self):
        return self.uri + '/(?=.)'

    def _create_docs_api(self, kong_client):
        response = kong_client \
            .apis.create(self.name + self._docs_suffix(),
                         upstream_url=self._docs_upstream(),
                         uris=self._docs_uri_pattern(),
                         hosts=self.hosts)
        self.docs_kong_id = response['id']

    def get_docs_kong_id(self):
        return str(self.docs_kong_id)

    @staticmethod
    def _docs_suffix():
        return '-doc'

    def _docs_upstream(self):
        doc_endpoint = reverse('api-doc', args=[self.name])
        return urllib.parse.urljoin(settings.KONG_TRAFFIC_URL, doc_endpoint)

    def _docs_uri_pattern(self):
        return self.uri + '/$'

    def update_kong(self, kong_client):
        self._update_docs_api(kong_client)
        return self._update_main_api(kong_client)

    def _update_main_api(self, kong_client):
        return kong_client \
            .apis.update(self.get_kong_id(),
                         upstream_url=self.upstream_url,
                         hosts=self.hosts,
                         uris=self._api_uri_pattern(),
                         strip_uri=self.strip_uri,
                         preserve_host=self.preserve_host)

    def _update_docs_api(self, kong_client):
        return kong_client \
            .apis.update(self.get_docs_kong_id(),
                         upstream_url=self._docs_upstream(),
                         uris=self._docs_uri_pattern(),
                         hosts=self.hosts)

    def delete_kong(self, kong_client):
        for plugin in self.plugins:
            plugin.kong_id = None
            plugin.save()

        self._delete_docs_api(kong_client)
        self._delete_main_api(kong_client)

    def _delete_main_api(self, kong_client):
        kong_client.apis.delete(self.get_kong_id())
        self.kong_id = None

    def _delete_docs_api(self, kong_client):
        kong_client.apis.delete(self.get_docs_kong_id())
        self.docs_kong_id = None

    @property
    def plugins(self):
        plugins = []

        try:
            plugins.append(self.kongpluginhttplog)
        except KongPluginHttpLog.DoesNotExist:
            pass
        try:
            plugins.append(self.kongpluginratelimiting)
        except KongPluginRateLimiting.DoesNotExist:
            pass
        try:
            plugins.append(self.kongpluginjwt)
        except KongPluginJwt.DoesNotExist:
            pass

        return plugins


# pylint: disable=invalid-name
@receiver(post_save, sender=KongApi)
def re_create_kong_plugins_when_re_enabling_existing_api(created, instance, *_, **__):
    if not created:
        for plugin in instance.plugins:
            plugin.save()


class KongPlugin(KongObject):

    plugin_name = None
    apidata = models.OneToOneField(KongApi, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def get_plugin_name(self):
        if self.plugin_name is None:
            raise ImproperlyConfigured("falta definir el nombre del plugin")

        return self.plugin_name

    @abstractmethod
    def config(self):
        pass

    def is_enabled(self):
        return super(KongPlugin, self).is_enabled() and self.apidata.enabled

    def create_kong(self, kong_client):
        return kong_client.plugins.create(self.get_plugin_name(),
                                          api_name_or_id=str(self.apidata.kong_id),
                                          config=self.config())

    def update_kong(self, kong_client):
        return kong_client.plugins.update(self.get_kong_id(),
                                          api_pk=str(self.apidata.kong_id),
                                          config=self.config())

    def delete_kong(self, kong_client):
        kong_client.plugins.delete(self.get_kong_id())
        self.kong_id = None


class KongConsumer(KongObject):

    api = models.ForeignKey(KongApi, on_delete=models.CASCADE)
    applicant = models.CharField(max_length=100, blank=False)
    contact_email = models.EmailField(blank=False)

    class Meta:
        unique_together = ('api', 'applicant')

    def username(self):
        return '%s@%s' % (self.applicant, self.api.name)

    def create_kong(self, kong_client):
        return kong_client.consumers.create(username=self.username())

    def update_kong(self, kong_client):
        return kong_client.consumers.update(self.get_kong_id(), username=self.username())

    def delete_kong(self, kong_client):
        kong_client.consumers.delete(self.get_kong_id())
        self.kong_id = False


class JwtCredential(KongObject):

    consumer = models.OneToOneField(KongConsumer, on_delete=models.CASCADE)
    key = models.CharField(max_length=100, null=True)
    secret = models.CharField(max_length=100, null=True)

    def create_kong(self, kong_client):
        if self.consumer.kong_id is None:
            raise ValidationError('cannot create a credential for a consumer with out kong id')

        json = self._send_create(kong_client)

        self.key = json['key']
        self.secret = json['secret']
        return json

    def _credential_endpoint(self, kong_client):
        url = urllib.parse.urljoin(kong_client.consumers.endpoint, self.consumer.get_kong_id())
        url += '/'
        url = urllib.parse.urljoin(url, 'jwt/')
        return url

    def _send_create(self, kong_client):
        endpoint = self._credential_endpoint(kong_client)

        response = requests.post(endpoint)
        json = response.json()
        if response.status_code != 201:
            raise ConnectionError(json)
        return json

    def delete_kong(self, kong_client):
        if self.consumer.kong_id is not None:
            self._send_delete(kong_client)

        self.kong_id = None

    def _send_delete(self, kong_client):
        endpoint = self._credential_endpoint(kong_client)

        response = requests.delete(endpoint + self.get_kong_id())
        if response.status_code != 204:
            raise ConnectionError()

    def update_kong(self, kong_client):
        return dict(id=self.kong_id)


PENDING = "PENDING"
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"
TOKEN_REQUEST_STATES = [
    (PENDING, 'Pendiente'),
    (ACCEPTED, 'Aceptada'),
    (REJECTED, 'Rechazada'),
]


class TokenRequest(models.Model):

    api = models.ForeignKey(KongApi, on_delete=models.CASCADE)
    applicant = models.CharField(max_length=100, blank=False)
    contact_email = models.EmailField(blank=False)
    consumer_application = models.CharField(max_length=200, blank=False)
    requests_per_day = models.IntegerField()
    state = models.CharField(default=PENDING,
                             choices=TOKEN_REQUEST_STATES,
                             max_length=20)

    def is_pending(self):
        return self.state == PENDING

    def accept(self):
        if not self.is_pending():
            raise ValidationError('only pending requests can be accepted')

        self.state = ACCEPTED
        self.save()

        token_request_accepted.send(sender=self.__class__, instance=self)

    def reject(self):
        if not self.is_pending():
            raise ValidationError('only pending requests can be rejected')

        self.state = REJECTED
        self.save()


class KongPluginRateLimiting(KongPlugin):

    plugin_name = 'rate-limiting'
    second = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    minute = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    hour = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    day = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def clean(self):
        if not self.enabled:
            return

        config = self.config()

        if not config:
            raise ValidationError('At least one of second, '
                                  'minute, hour, or day values'
                                  ' must be provided')

        prev_k = None
        prev_v = 0
        for key, value in config.items():
            if value < prev_v:
                raise ValidationError('The limit for %s cannot be lower '
                                      'than the limit for %s' % (key, prev_k))
            prev_k = key
            prev_v = value

    def config(self):
        config = {'second': self.second,
                  'minute': self.minute,
                  'hour': self.hour,
                  'day': self.day}

        cleaned_config = {}
        for key, value in config.items():
            if value:
                cleaned_config[key] = value

        return cleaned_config


class KongPluginHttpLog(KongPlugin):

    plugin_name = API_GATEWAY_LOG_PLUGIN_NAME
    api_key = models.CharField(max_length=100, blank=False, null=False)
    exclude_regex = models.CharField(max_length=100, null=False, blank=True)

    def config(self):
        return {'token': self.api_key,
                'endpoint': settings.HTTPLOG2_ENDPOINT,
                'api_data': self.apidata.pk}


class KongPluginJwt(KongPlugin):

    plugin_name = 'jwt'

    def config(self):
        return {}


@receiver(pre_save, sender=KongApi)
@receiver(pre_save, sender=KongPluginRateLimiting)
@receiver(pre_save, sender=KongPluginHttpLog)
@receiver(pre_save, sender=KongPluginJwt)
@receiver(pre_save, sender=KongConsumer)
@receiver(pre_save, sender=JwtCredential)
def manage_kong_on_save(instance, *_, **__):
    instance.manage_kong(kong_client_using_settings())


@receiver(pre_delete, sender=KongApi)
@receiver(pre_delete, sender=KongPluginRateLimiting)
@receiver(pre_delete, sender=KongPluginHttpLog)
@receiver(pre_delete, sender=KongPluginJwt)
@receiver(pre_delete, sender=KongConsumer)
@receiver(pre_delete, sender=JwtCredential)
def delete_kong_on_delete(instance, *_, **__):
    instance.delete_kong(kong_client_using_settings())


@receiver(token_request_accepted, sender=TokenRequest)
def token_request_accepted_handler(instance, *_, **__):

    consumer = KongConsumer(enabled=True,
                            api=instance.api,
                            applicant=instance.applicant,
                            contact_email=instance.contact_email)

    consumer.save()1

    JwtCredential(enabled=True,
                  consumer=consumer).save()
