from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


# Mock the check method of the Command
@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    """Test Commands"""
    def test_wait_for_db_ready(self, patched_check):
        """Test Database Ready Immediately"""
        # Simulates the database being ready by mocking
        patched_check.return_value = True

        call_command('wait_for_db')  # Runs management command
        # Verify that the check method was called exactly once,
        # with the correct parameters
        patched_check.assert_called_once_with(databases=['default'])

    # Patch the sleep function to return nothing and avoid waiting
    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError"""
        # First 2 calls will raise Psycopg2Error (PostgreSQL isn't ready)
        # Next 3 calls will raise OperationalError (Django can't connect to DB)
        # 6th call will return True
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 3 + [True]

        call_command('wait_for_db')
        # Verify that the check method was called 6 times
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=['default'])
