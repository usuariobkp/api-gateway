import pytest
from django.conf import settings

from api_management.apps.analytics.test.support import custom_faker
from api_management.apps.api_registry.models import KongPluginCors
from api_management.apps.api_registry.test.support import generate_api_data


# pylint: disable=redefined-outer-name

@pytest.fixture()
def cfaker():
    return custom_faker()


@pytest.fixture()
def api_data(cfaker):
    api = generate_api_data(name=cfaker.api_name(), upstream_url=cfaker.url(),
                            uris=cfaker.api_path(), kong_id=None, api_id=cfaker.random_int())
    return api


@pytest.fixture()
def apis_kong_client(cfaker, mocker):
    def create_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
        return {'id': cfaker.kong_id()}

    def update_side_effect(a_id, *args, **kwargs):  # pylint: disable=unused-argument
        return {'id': a_id}

    stub = mocker.stub(name='apis_kong_client')
    stub.create = mocker.stub(name='apis_kong_client_create_stub')
    stub.create.side_effect = create_side_effect
    stub.update = mocker.stub(name='apis_kong_client_update_stub')
    stub.update.side_effect = update_side_effect
    stub.delete = mocker.stub(name='apis_kong_client_delete_stub')
    return stub


@pytest.fixture()
def plugins_kong_client(mocker, cfaker):
    def create_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
        return {'id': cfaker.kong_id()}

    stub = mocker.stub(name='plugins_kong_client')

    stub.create = mocker.stub(name='plugins_kong_client_create_stub')
    stub.create.side_effect = create_side_effect

    stub.delete = mocker.stub(name='plugins_kong_client_delete_stub')

    stub.list = mocker.stub(name='plugins_kong_client_list_stub')
    stub.list.return_value = []
    return stub


@pytest.fixture()
def kong_client(plugins_kong_client, apis_kong_client, mocker):
    stub = mocker.stub(name='kong_client_stub')
    stub.apis = apis_kong_client
    stub.plugins = plugins_kong_client
    return stub


@pytest.fixture()
def kong_traffic_url():
    return settings.KONG_TRAFFIC_URL


@pytest.fixture()
def httplog2_endpoint(cfaker):
    return cfaker.url()


@pytest.fixture()
def cors_plugin(cfaker, api_data):
    api_data.enabled = True
    api_data.save()

    cors_plugin = KongPluginCors.objects.get(apidata=api_data)
    cors_plugin.enabled = True
    cors_plugin.origins = cfaker.uri()

    return cors_plugin
