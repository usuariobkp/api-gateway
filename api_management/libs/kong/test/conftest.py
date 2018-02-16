# pylint: disable=no-name-in-module
from http.client import OK, CREATED, CONFLICT, NO_CONTENT
from faker import Faker
import pytest

from django.conf import settings

from api_management.libs.providers.providers import CustomInfoProvider
from ..client import APIAdminClient

API_URL = settings.KONG_ADMIN_URL


@pytest.fixture()
def fake():
    a_faker = Faker()
    a_faker.add_provider(CustomInfoProvider)
    return a_faker


NAMES = []


@pytest.fixture
def created_names():
    return NAMES


@pytest.fixture
def already_exists_response(mocker):
    response = mocker.stub(name='response_stub')
    response.status_code = CONFLICT
    response.content = "name already exists"
    return response


@pytest.fixture
def missing_fields_response(mocker):
    response = mocker.stub(name='response_stub')
    response.status_code = 400
    response.content = "missing parameter"
    return response


@pytest.fixture
def invalid_value_response(mocker):
    response = mocker.stub(name='response_stub')
    response.status_code = 400
    response.content = "invalid parameter"
    return response


def satisfy_required_fields(dictionary):
    required_fields = ['uris', 'hosts']
    valid = False
    for key in dictionary:
        valid = valid or (key in required_fields and dictionary[key] is not None)
    return valid


def valid_value_type(value):
    return isinstance(value, (bool, str)) \
           or value is None


def preserve_host_validator(value):
    valid_str = ['true', 'false']
    return value is None \
        or isinstance(value, bool) \
        or (isinstance(value, str)
            and value.lower() in valid_str)


def satisfy_valid_values(dictionary):
    valid_keys = {'name': valid_value_type,
                  'hosts': valid_value_type,
                  'uris': valid_value_type,
                  'methods': valid_value_type,
                  'upstream_url': valid_value_type,
                  'strip_uri': valid_value_type,
                  'preserve_host': preserve_host_validator}
    for k, val in dictionary.items():
        if not (k in valid_keys and valid_keys[k](val)):
            return False
    return True


@pytest.fixture
# pylint: disable=redefined-outer-name, too-many-arguments
def session_stub(mocker, fake, created_names,
                 already_exists_response, missing_fields_response,
                 invalid_value_response):
    def post_side_effect(_, **kwargs):
        if kwargs['data']['name'] in created_names:
            return already_exists_response

        if not satisfy_required_fields(kwargs['data']):
            return missing_fields_response

        if not satisfy_valid_values(kwargs['data']):
            return invalid_value_response

        created_names.append(kwargs['data']['name'])
        response = mocker.stub(name='response_stub')
        response.status_code = CREATED
        kong_id = fake.kong_id()
        id_dict = {'id': kong_id}
        response.json = lambda: {**id_dict, **kwargs['data']}
        return response

    def patch_side_effect(_, **kwargs):
        response = mocker.stub(name='response_stub')
        response.status_code = OK
        response.json = lambda: kwargs['data']
        return response

    def get_side_effect(_, **kwargs):  # pylint: disable=unused-argument
        response = mocker.stub(name='response_stub')
        response.status_code = OK
        apis = []
        for name in created_names:
            apis.append({'name': name})
        response.json = lambda: {'data': apis}
        return response

    def delete_side_effect(_, **kwargs):  # pylint: disable=unused-argument
        response = mocker.stub(name='response_stub')
        response.status_code = NO_CONTENT
        return response

    stub = mocker.stub(name='session_stub')
    stub.post = mocker.stub(name='session_post_stub')
    stub.post.side_effect = post_side_effect
    stub.patch = mocker.stub(name='session_patch_stub')
    stub.patch.side_effect = patch_side_effect
    stub.delete = mocker.stub(name='session_delete_stub')
    stub.delete.side_effect = delete_side_effect
    stub.get = mocker.stub(name='session_get_stub')
    stub.get.side_effect = get_side_effect
    return stub


@pytest.fixture
# pylint: disable=redefined-outer-name
def requests_stub(mocker, session_stub):
    stub = mocker.stub(name='requests_stub')
    stub.session = mocker.stub(name='requests_session_stub')
    stub.session.side_effect = lambda **kwargs: session_stub
    return stub


@pytest.fixture
# pylint: disable=redefined-outer-name
def kong(requests_stub):
    NAMES.clear()
    return APIAdminClient(API_URL, requests_module=requests_stub)


@pytest.fixture
def kong_admin_url():
    return API_URL


@pytest.fixture
def invalid_value(fake):  # pylint: disable=redefined-outer-name
    return fake.word()
