import logging
from functools import partial

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from sqlalchemy import exc
from sqlalchemy import event
from sqlalchemy.pool import manage
from sqlalchemy.pool import Pool
from sqlalchemy.event import listens_for

from django.db.models.sql import compiler
from django.db.models.sql.constants import MULTI


POOL_PESSIMISTIC_MODE = getattr(settings, "DJORM_POOL_PESSIMISTIC", False)
POOL_SETTINGS = getattr(settings, 'DJORM_POOL_OPTIONS', {})
POOL_SETTINGS.setdefault("recycle", 3600)

logger = logging.getLogger('djorm.pool')


@event.listens_for(Pool, "checkout")
def _on_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug("connection retrieved from pool")

    if POOL_PESSIMISTIC_MODE:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SELECT 1")
        except:
            # raise DisconnectionError - pool will try
            # connecting again up to three times before raising.
            raise exc.DisconnectionError()
        finally:
            cursor.close()


@event.listens_for(Pool, "checkin")
def _on_checkin(*args, **kwargs):
    logger.debug("connection returned to pool")


@event.listens_for(Pool, "connect")
def _on_connect(*args, **kwargs):
    logger.debug("connection created")


def patch_mysql():
    class hashabledict(dict):
        def __hash__(self):
            return hash(frozenset(self))
            #return hash(tuple(sorted(self.items())))

    class hashablelist(list):
        def __hash__(self):
            return hash(tuple(sorted(self)))

    class ManagerProxy(object):
        def __init__(self, manager):
            self.manager = manager

        def __getattr__(self, key):
            return getattr(self.manager, key)

        def connect(self, *args, **kwargs):
            if 'conv' in kwargs:
                conv = kwargs['conv']
                if isinstance(conv, dict):
                    items = []
                    for k, v in conv.items():
                        if isinstance(v, list):
                            v = hashablelist(v)
                        items.append((k, v))
                    kwargs['conv'] = hashabledict(items)
            if 'ssl' in kwargs:
                ssl = kwargs['ssl']
                if isinstance(ssl, dict):
                    items = []
                    for k, v in ssl.items():
                        if isinstance(v, list):
                            v = hashablelist(v)
                        items.append((k, v))
                    kwargs['ssl'] = hashabledict(items)
            return self.manager.connect(*args, **kwargs)

    try:
        from django.db.backends.mysql import base as mysql_base
    except (ImproperlyConfigured, ImportError) as e:
        return

    if not hasattr(mysql_base, "_Database"):
        mysql_base._Database = mysql_base.Database
        mysql_base.Database = ManagerProxy(manage(mysql_base._Database, **POOL_SETTINGS))


def patch_postgresql():
    try:
        from django.db.backends.postgresql import base as pgsql_base
    except (ImproperlyConfigured, ImportError) as e:
        return

    if not hasattr(pgsql_base, "_Database"):
        pgsql_base._Database = pgsql_base.Database
        pgsql_base.Database = manage(pgsql_base._Database, **POOL_SETTINGS)


def patch_sqlite3():
    try:
        from django.db.backends.sqlite3 import base as sqlite3_base
    except (ImproperlyConfigured, ImportError) as e:
        return

    if not hasattr(sqlite3_base, "_Database"):
        sqlite3_base._Database = sqlite3_base.Database
        sqlite3_base.Database = manage(sqlite3_base._Database, **POOL_SETTINGS)


def install_django_orm_patch():
    """
    在访问完数据库后，马上归还连接，而不是在请求完成时再归还。
    :return:
    """
    execute_sql = compiler.SQLCompiler.execute_sql

    # Django 1.11
    def patched_execute_sql(self, *args, **kwargs):
        result = execute_sql(self, *args, **kwargs)
        if not self.connection.in_atomic_block:
            self.connection.close()  # return connection to pool by db_pool_patch
        return result

    compiler.SQLCompiler.execute_sql = patched_execute_sql

    insert_execute_sql = compiler.SQLInsertCompiler.execute_sql

    def patched_insert_execute_sql(self, return_id=False):
        result = insert_execute_sql(self, return_id)
        if not self.connection.in_atomic_block:
            self.connection.close()  # return connection to pool by db_pool_patch
        return result

    compiler.SQLInsertCompiler.execute_sql = patched_insert_execute_sql

def patch_all():
    patch_mysql()
    patch_postgresql()
    patch_sqlite3()
    install_django_orm_patch()


patch_all()