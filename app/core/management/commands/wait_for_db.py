"""
Command to wait the for the postgres to be available
"""
import time

from psycopg2 import OperationalError as Psycopg2OperationalError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write('Waiting for database...')
        db_up = False
        while db_up is False:
            try:
                self.check_health()
                db_up = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS('Database available!'))

    def check_health(self):
        try:
            self.check(databases=['default'])
            self.attempt_query()
        except (Psycopg2OperationalError, OperationalError) as e:
            raise e

    def attempt_query(self):
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            one = cursor.fetchone()[0]
            if one != 1:
                raise OperationalError
