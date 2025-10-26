"""
Comprehensive test suite for Flask filter utilities.

Tests the localtime() filter and register_filters() function with full coverage of:
- UTC datetime conversion to various timezones
- None value handling
- String format validation (YYYY-MM-DD HH:MM)
- App config TIMEZONE setting support
- Filter registration with Flask app
- Template context integration

Target: 100% coverage of app/utils/filters.py (16 lines)
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo


class TestLocaltimeFilter:
    """Tests for the localtime() filter function."""

    def test_convert_utc_datetime_to_default_timezone_utc(self, app):
        """
        Test converting UTC datetime to default timezone (UTC).

        Scenario: Pass UTC datetime with no custom timezone
        App config TIMEZONE not set (defaults to 'UTC')
        Verify: Returns formatted string in UTC
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 14, 30, 45, tzinfo=ZoneInfo('UTC'))

        # Act
        result = localtime(utc_datetime)

        # Assert
        assert result == '2024-05-15 14:30'
        assert isinstance(result, str)

    def test_convert_utc_datetime_to_custom_timezone_america_new_york(self, app):
        """
        Test converting UTC datetime to America/New_York timezone.

        Scenario: UTC 14:30 converts to America/New_York timezone
        Verify: Time adjusted correctly (UTC-4 or UTC-5 depending on DST)
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act: May 15, 2024 is during EDT (UTC-4)
        result = localtime(utc_datetime, tz='America/New_York')

        # Assert: 14:30 UTC = 10:30 EDT
        assert result == '2024-05-15 10:30'

    def test_convert_utc_datetime_to_europe_london_timezone(self, app):
        """
        Test converting UTC datetime to Europe/London timezone.

        Scenario: UTC datetime converts to Europe/London timezone
        Verify: Time adjusted correctly (UTC+0 or UTC+1 depending on BST)
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act: May 15, 2024 is during BST (UTC+1)
        result = localtime(utc_datetime, tz='Europe/London')

        # Assert: 14:30 UTC = 15:30 BST
        assert result == '2024-05-15 15:30'

    def test_handle_none_value_returns_empty_string(self, app):
        """
        Test that None value returns an empty string.

        Scenario: localtime(None) called
        Verify: Returns empty string, no error
        """
        # Arrange
        from app.utils.filters import localtime

        # Act
        result = localtime(None)

        # Assert
        assert result == ''
        assert isinstance(result, str)

    def test_verify_string_format_year_month_day_hour_minute(self, app):
        """
        Test that output format matches YYYY-MM-DD HH:MM.

        Scenario: Convert various datetimes
        Verify: All follow format YYYY-MM-DD HH:MM (exactly 16 characters)
        """
        # Arrange
        from app.utils.filters import localtime
        test_datetimes = [
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=ZoneInfo('UTC')),
            datetime(2024, 12, 31, 23, 59, 0, tzinfo=ZoneInfo('UTC')),
            datetime(2020, 2, 29, 12, 15, 0, tzinfo=ZoneInfo('UTC')),  # Leap year
        ]

        # Act & Assert
        for dt in test_datetimes:
            result = localtime(dt)
            # Format: YYYY-MM-DD HH:MM = 16 characters
            assert len(result) == 16
            # Verify format with regex-like check
            parts = result.split(' ')
            assert len(parts) == 2
            date_part = parts[0]
            time_part = parts[1]
            assert date_part.count('-') == 2  # YYYY-MM-DD
            assert time_part.count(':') == 1  # HH:MM

    def test_convert_midnight_utc_time(self, app):
        """
        Test conversion of midnight UTC time.

        Scenario: UTC midnight (00:00)
        Verify: Displays as 00:00
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 0, 0, 0, tzinfo=ZoneInfo('UTC'))

        # Act
        result = localtime(utc_datetime)

        # Assert
        assert result == '2024-05-15 00:00'

    def test_convert_noon_utc_time(self, app):
        """
        Test conversion of noon UTC time.

        Scenario: UTC noon (12:00)
        Verify: Displays as 12:00
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 12, 0, 0, tzinfo=ZoneInfo('UTC'))

        # Act
        result = localtime(utc_datetime)

        # Assert
        assert result == '2024-05-15 12:00'

    def test_use_timezone_from_app_config_when_not_provided(self, app):
        """
        Test that app config TIMEZONE is used when tz parameter not provided.

        Scenario: Set app.config['TIMEZONE'] = 'Europe/Paris'
        Call localtime() without tz parameter
        Verify: Uses TIMEZONE from config
        """
        # Arrange
        from app.utils.filters import localtime
        with app.app_context():
            app.config['TIMEZONE'] = 'Europe/Paris'
            utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

            # Act
            result = localtime(utc_datetime)

            # Assert: 14:30 UTC = 16:30 CEST (UTC+2 in May)
            assert result == '2024-05-15 16:30'

    def test_provided_tz_overrides_app_config_timezone(self, app):
        """
        Test that explicit tz parameter overrides app config TIMEZONE.

        Scenario: app.config['TIMEZONE'] = 'UTC', but call with tz='Asia/Tokyo'
        Verify: Uses provided tz parameter
        """
        # Arrange
        from app.utils.filters import localtime
        with app.app_context():
            app.config['TIMEZONE'] = 'UTC'
            utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

            # Act
            result = localtime(utc_datetime, tz='Asia/Tokyo')

            # Assert: 14:30 UTC = 23:30 JST (UTC+9)
            assert result == '2024-05-15 23:30'

    def test_winter_time_timezone_conversion_america_new_york(self, app):
        """
        Test timezone conversion during winter (EST, UTC-5).

        Scenario: Winter datetime (January) in America/New_York
        Verify: Correct offset applied (EST is UTC-5)
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 1, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act: January is EST (UTC-5)
        result = localtime(utc_datetime, tz='America/New_York')

        # Assert: 14:30 UTC = 09:30 EST
        assert result == '2024-01-15 09:30'

    def test_summer_time_timezone_conversion_europe_london(self, app):
        """
        Test timezone conversion during summer (BST, UTC+1).

        Scenario: Summer datetime (July) in Europe/London
        Verify: Correct offset applied (BST is UTC+1)
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 7, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act: July is BST (UTC+1)
        result = localtime(utc_datetime, tz='Europe/London')

        # Assert: 14:30 UTC = 15:30 BST
        assert result == '2024-07-15 15:30'

    def test_leading_zeros_in_time_format(self, app):
        """
        Test that single-digit hours and minutes include leading zeros.

        Scenario: Early morning time with single digits (e.g., 01:05)
        Verify: Leading zeros present
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 1, 5, 0, tzinfo=ZoneInfo('UTC'))

        # Act
        result = localtime(utc_datetime)

        # Assert: Must have leading zeros
        assert result == '2024-05-15 01:05'
        assert '01:05' in result
        assert '1:5' not in result

    def test_seconds_are_not_included_in_output(self, app):
        """
        Test that seconds are truncated in output (not included in format).

        Scenario: Datetime with seconds: 14:30:45
        Verify: Output is 14:30 (seconds discarded)
        """
        # Arrange
        from app.utils.filters import localtime
        utc_datetime = datetime(2024, 5, 15, 14, 30, 45, tzinfo=ZoneInfo('UTC'))

        # Act
        result = localtime(utc_datetime)

        # Assert
        assert result == '2024-05-15 14:30'
        assert ':45' not in result


class TestRegisterFilters:
    """Tests for the register_filters() function."""

    def test_register_localtime_filter_with_app(self, app):
        """
        Test that localtime filter is registered with Flask app.

        Scenario: Call register_filters(app)
        Verify: 'localtime' exists in app.jinja_env.filters
        """
        # Arrange
        from app.utils.filters import register_filters
        test_app = app

        # Act
        # Filter should already be registered in conftest.py app fixture
        # but we verify it exists

        # Assert
        assert 'localtime' in test_app.jinja_env.filters
        assert callable(test_app.jinja_env.filters['localtime'])

    def test_registered_filter_is_callable(self, app):
        """
        Test that the registered localtime filter is callable.

        Scenario: Get localtime from jinja_env.filters
        Verify: It's a callable function
        """
        # Arrange
        test_app = app

        # Act
        filter_func = test_app.jinja_env.filters.get('localtime')

        # Assert
        assert filter_func is not None
        assert callable(filter_func)

    def test_registered_filter_can_be_called_with_datetime(self, app):
        """
        Test that registered filter works with datetime argument.

        Scenario: Call filter with datetime object
        Verify: Returns formatted string
        """
        # Arrange
        from datetime import datetime
        from zoneinfo import ZoneInfo
        test_app = app
        filter_func = test_app.jinja_env.filters['localtime']
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act
        result = filter_func(utc_datetime)

        # Assert
        assert result == '2024-05-15 14:30'

    def test_registered_filter_can_be_called_with_none(self, app):
        """
        Test that registered filter handles None value correctly.

        Scenario: Call filter with None
        Verify: Returns empty string
        """
        # Arrange
        test_app = app
        filter_func = test_app.jinja_env.filters['localtime']

        # Act
        result = filter_func(None)

        # Assert
        assert result == ''

    def test_registered_filter_accepts_timezone_parameter(self, app):
        """
        Test that registered filter accepts timezone parameter.

        Scenario: Call filter with datetime and tz parameter
        Verify: Timezone parameter is applied
        """
        # Arrange
        from datetime import datetime
        from zoneinfo import ZoneInfo
        test_app = app
        filter_func = test_app.jinja_env.filters['localtime']
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Act
        result = filter_func(utc_datetime, tz='America/New_York')

        # Assert: 14:30 UTC = 10:30 EDT
        assert result == '2024-05-15 10:30'

    def test_filter_available_in_template_context(self, client):
        """
        Test that localtime filter is available in template rendering context.

        Scenario: Render a test template that uses localtime filter
        Verify: Filter is accessible and works in Jinja2 template
        """
        # Arrange: Create a test route that uses the filter
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from flask import render_template_string

        test_app = client.application
        with test_app.app_context():
            template_string = "{{ dt | localtime }}"
            test_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

            # Act
            result = render_template_string(template_string, dt=test_datetime)

            # Assert
            assert result == '2024-05-15 14:30'

    def test_filter_with_timezone_parameter_in_template(self, client):
        """
        Test that localtime filter with timezone parameter works in template.

        Scenario: Use filter in template with custom timezone
        Verify: Timezone parameter works in Jinja2 context
        """
        # Arrange
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from flask import render_template_string

        test_app = client.application
        with test_app.app_context():
            # Jinja2 allows passing keyword arguments to filters
            template_string = "{{ dt | localtime('America/New_York') }}"
            test_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

            # Act
            result = render_template_string(template_string, dt=test_datetime)

            # Assert: 14:30 UTC = 10:30 EDT
            assert result == '2024-05-15 10:30'

    def test_multiple_filter_registrations_dont_break(self, app):
        """
        Test that calling register_filters multiple times doesn't break.

        Scenario: Call register_filters(app) multiple times
        Verify: No errors, filter still works correctly
        """
        # Arrange
        from app.utils.filters import register_filters
        from datetime import datetime
        from zoneinfo import ZoneInfo
        test_app = app

        # Act: Register multiple times
        register_filters(test_app)
        register_filters(test_app)
        register_filters(test_app)

        filter_func = test_app.jinja_env.filters['localtime']
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Assert: Filter still works after multiple registrations
        result = filter_func(utc_datetime)
        assert result == '2024-05-15 14:30'

    def test_register_filters_with_custom_app_instance(self, app):
        """
        Test that register_filters works with a custom Flask app instance.

        Scenario: Create a new Flask app and register filters
        Verify: Filters are added to the custom app
        """
        # Arrange
        from flask import Flask
        from app.utils.filters import register_filters
        from datetime import datetime
        from zoneinfo import ZoneInfo

        custom_app = Flask(__name__)

        # Act
        register_filters(custom_app)

        # Assert
        assert 'localtime' in custom_app.jinja_env.filters
        filter_func = custom_app.jinja_env.filters['localtime']
        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))
        result = filter_func(utc_datetime)
        assert result == '2024-05-15 14:30'

    def test_filter_registration_preserves_existing_filters(self, app):
        """
        Test that registering new filters doesn't remove existing ones.

        Scenario: App has existing filters, then register localtime
        Verify: Existing filters still present
        """
        # Arrange
        from app.utils.filters import register_filters
        test_app = app

        # Store existing filters
        existing_filters_before = set(test_app.jinja_env.filters.keys())

        # Act
        register_filters(test_app)

        # Assert
        existing_filters_after = set(test_app.jinja_env.filters.keys())
        # All existing filters should still be there
        assert existing_filters_before.issubset(existing_filters_after)
        # And localtime should be present
        assert 'localtime' in existing_filters_after

    def test_filter_name_is_exactly_localtime(self, app):
        """
        Test that filter is registered with exact name 'localtime'.

        Scenario: Check filter dictionary keys
        Verify: 'localtime' key exists (not 'local_time' or 'localize' etc.)
        """
        # Arrange
        test_app = app

        # Act
        filter_keys = list(test_app.jinja_env.filters.keys())

        # Assert
        assert 'localtime' in filter_keys
        # Verify exact name
        assert any(key == 'localtime' for key in filter_keys)

    def test_filter_function_is_localtime_from_module(self, app):
        """
        Test that registered filter is the localtime function from module.

        Scenario: Compare registered filter with imported function
        Verify: They reference the same function
        """
        # Arrange
        from app.utils.filters import localtime
        test_app = app
        registered_filter = test_app.jinja_env.filters['localtime']

        # Act & Assert
        # The registered filter should be the localtime function
        # (Note: it might be wrapped, so we verify it has the right behavior)
        from datetime import datetime
        from zoneinfo import ZoneInfo

        utc_datetime = datetime(2024, 5, 15, 14, 30, 0, tzinfo=ZoneInfo('UTC'))

        # Both should produce the same result
        assert localtime(utc_datetime) == registered_filter(utc_datetime)
