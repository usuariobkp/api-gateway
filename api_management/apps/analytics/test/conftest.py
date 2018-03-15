import pytest
from faker import Faker


@pytest.fixture
def user(db):  # pylint: disable=invalid-name, unused-argument, redefined-outer-name
    """
    Create a test user.
    """
    from django.contrib.auth.models import User
    a_user = User.objects.create_user('test', 'test@github.com', 'test')

    return a_user


@pytest.fixture
def staff_user(user):  # pylint: disable=unused-argument, redefined-outer-name, invalid-name
    """
    Create a test staff user.
    """
    user.is_staff = True
    return user


@pytest.fixture
def well_formed_query():
    faker = Faker()
    return {
        "ip_address": faker.ipv4(),
        "host": faker.domain_name(),
        "uri": faker.uri_path(),
        "querystring": faker.text(),
        "start_time": faker.iso8601(),
        "request_time": 0.5,
        "status_code": 200,
    }
