"""
Test custom management commands.
"""
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2OperationalError

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
@patch('core.management.commands.wait_for_db.Command.attempt_query')
class CommandTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self,
                               patched_attempt_query,
                               patched_check_health):
        """Test waiting for database if database ready."""
        patched_check_health.return_value = True
        patched_attempt_query.return_value = None

        call_command('wait_for_db')

        patched_check_health.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep,
                               patched_attempt_query,
                               patched_check_health):
        """Test waiting for database when getting Errors at first times."""
        patched_check_health.side_effect = [Psycopg2OperationalError] * 2 + \
            [OperationalError] * 3 + [True]
        patched_sleep.return_value = None
        patched_attempt_query.return_value = None

        call_command('wait_for_db')

        self.assertEqual(patched_check_health.call_count, 6)
        patched_check_health.assert_called_with(databases=['default'])
