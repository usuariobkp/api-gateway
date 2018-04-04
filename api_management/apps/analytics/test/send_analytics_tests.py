from unittest.mock import MagicMock

from urllib.parse import parse_qsl
import pytest
import requests_mock


def test_send_analytics(ga_manager, tracking_id, query):
    with requests_mock.mock() as rmock:
        # Setup
        rmock.post(requests_mock.ANY, status_code=200)

        # Exercise
        ga_manager.send_analytics(query)

        # Verify
        history = rmock.request_history
        assert len(history) == 1

        request = history[0]
        assert request.method == 'POST'
        assert request.url == 'http://www.google-analytics.com/collect'

        expected_data = {'v': 1,  # Protocol Version
                         'cid': query.id,  # Client ID
                         'tid': tracking_id,  # Tracking ID
                         't': 'pageview',  # Hit Type
                         'uip': query.ip_address,  # User IP override
                         'dh': query.host,  # Document HostName
                         'dp': query.uri,  # Document Path
                         'cd1': query.querystring,  # Custom Dimention
                         'srt': query.request_time,  # Server Response Time
                         'cm1': query.start_time,  # Custom Metric
                         'cm2': query.status_code,  # Custom Metric
                         'cd3': query.api_data.name,
                         'cm3': query.api_data.pk}

        for key, val in expected_data.items():
            expected_data[key] = str(val)

        assert dict(parse_qsl(request.text)) == expected_data


MATCHING_REGEX_URI_PAIRS = [('regex', '/api/regex/test/'),
                            ('static', '/api/static/resource'),
                            ('media', '/media')]


#  pylint: disable=invalid-name
@pytest.mark.parametrize("regex,uri", MATCHING_REGEX_URI_PAIRS)
def test_if_exclude_regex_matches_query_uri_send_analyitics_you_must_not(ga_manager, query,
                                                                         regex, uri):
    exercise_manage_query(ga_manager, query, regex, uri)

    # Verify
    ga_manager.send_analytics.assert_not_called()


NON_MATCHING_REGEX_URI_PAIRS = [('', '/path/'),
                                ('no-match', '/path/'),
                                ('no-match', '')]


#  pylint: disable=invalid-name
@pytest.mark.parametrize("regex,uri", NON_MATCHING_REGEX_URI_PAIRS)
def test_if_exclude_regex_does_not_matches_query_uri_send_analyitics_you_must(ga_manager, query,
                                                                              regex, uri):
    exercise_manage_query(ga_manager, query, regex, uri)

    # Verify
    ga_manager.send_analytics.assert_called_once_with(query)


def exercise_manage_query(ga_manager, query, regex, uri):
    # Setup
    ga_manager.send_analytics = MagicMock()
    query.api_data.httplog2_ga_exclude_regex = regex
    query.uri = uri

    # Exercise
    ga_manager.manage_query(query)