import pytest
from faker import Faker

from api_management.libs.providers.providers import CustomInfoProvider

from ..models import ApiData


@pytest.fixture()
def faker():
    a_faker = Faker()
    a_faker.add_provider(CustomInfoProvider)
    return a_faker


@pytest.fixture()
def api_data(faker):  # pylint: disable=redefined-outer-name
    return ApiData(name=faker.api_name(),
                   upstream_url=faker.url(),
                   uris=faker.api_path(),
                   kong_id=None)


@pytest.fixture()
def kong_client(faker, mocker):  # pylint: disable=redefined-outer-name

    def create_side_effect(*args, **kwargs):  # pylint: disable=unused-argument
        return {'id': faker.kong_id()}

    stub = mocker.stub(name='kong_client_stub')
    stub.create = mocker.stub(name='kong_client_create_stub')
    stub.create.side_effect = create_side_effect
    stub.update = mocker.stub(name='kong_client_update_stub')
    stub.delete = mocker.stub(name='kong_client_delete_stub')
    return stub
