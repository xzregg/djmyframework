# -*- coding: utf-8 -*-
# @Time    : 2021-02-25 11:00
# @Author  : xzr
# @File    : sql
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :
import copy
import hashlib
import re
from math import ceil

import sqlparse
from django.core.cache import cache
from django.db import connections, connection
from django.db.models.sql.query import Query
from django.db.models import Q, Model
from django.db.models.sql.compiler import SQLCompiler
from django.utils.functional import cached_property
from pymysql.converters import escape_item
from sqlparse.sql import Identifier, IdentifierList
from sqlparse.tokens import Name


def get_table_name(tokens):
    for token in tokens:
        if token.ttype is None:
            return token.value
    return " "


def get_parent_table_name(tokens):
    for i, token in enumerate(tokens):
        if token.value.lower() == 'like':
            parent_table_name = tokens[i + 1].value
            return parent_table_name
    return ''


def get_table_columns(tokens):
    columns = set()
    for token in tokens:

        if isinstance(token, (IdentifierList, Identifier)):
            columns |= get_table_columns(token.tokens)
        if token.ttype is Name:
            columns.add(token.value.strip('`'))
            break
    return set(columns)


def get_ddl_table_info(sql_texts):
    result = {}

    parse = sqlparse.parse(sql_texts)
    for stmt in parse:
        # Get all the tokens except whitespaces
        tokens = [t for t in sqlparse.sql.TokenList(stmt.tokens) if t.ttype != sqlparse.tokens.Whitespace]
        is_create_stmt = False
        parent_table_name = ''
        table_name = ''
        for i, token in enumerate(tokens):
            # Is it a create statements ?
            if token.match(sqlparse.tokens.DDL, 'CREATE'):
                is_create_stmt = True
                table_name = get_table_name(tokens[i:])
                result.setdefault(table_name, set())
                parent_table_name = get_parent_table_name(tokens)
                if parent_table_name:
                    result[table_name] = copy.copy(result.get(parent_table_name, set()))
                continue

            # If it was a create statement and the current token starts with "("
            if is_create_stmt and token.value.startswith("("):
                columns = get_table_columns(token.tokens)
                result[table_name] |= columns

    return result



safe_sql_pattern = re.compile(r"""'|"|;|>|<|%|--""", flags=re.I)

def get_safe_sql_value(value):
    """防止sql注入"""
    value = re.sub(safe_sql_pattern, '', str(value))
    return value


def safe_value(value, charset='utf8mb4') -> str:
    """pymysql %s 的防止 sql 注入
    safe_value(1) -> '1'
    safe_value("1") -> "'1'"
    safe_value([1,2,3,4]) ->  '(1,2,3,4)'
    safe_value(datetime.datetime.now()) ->  "'2024-11-27 16:04:00.542974'"
    """
    return escape_item(value, charset)

sv = safe_value


def fetch_data_in_batches(cursor, batch_size=5000):
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        for row in rows:
            yield row

def dict_fetchall(cursor, batch_size=5000):
    """将游标返回的结果保存到一个字典对象中"""
    desc = cursor.description
    return (dict(zip([col[0] for col in desc], row))
            for row in fetch_data_in_batches(cursor, batch_size)
            )

def execute_raw_sql(sql, alias='readonly', use_dict=True, is_generator=False, batch_size=5000):
    conn = connections[alias]
    cursor = conn.cursor()
    cursor.execute(sql)
    if use_dict:
        return dict_fetchall(cursor, batch_size=batch_size)
    if is_generator:
        return fetch_data_in_batches(cursor, batch_size=batch_size)
    return cursor.fetchall()


def insert_many_to_many_sql(tabel_name, field_name1, field_name2, insert_data):
    """
    :param tabel_name: 表名
    :param field_name1: 字段1
    :param field_name2: 字段2
    :param insert_data: 插入数据{1: [1,2], 2: [1,2}
    :return:
    """
    sql = """INSERT IGNORE INTO `{tabel_name}` (`{field_name1}`, `{field_name2}`) VALUES """.format(tabel_name=tabel_name,
                                                                                                    field_name1=field_name1,
                                                                                                    field_name2=field_name2)
    for field1, field2_list in insert_data.items():
        for field2 in field2_list:
            sql += f"({field1},{field2}),"
    sql = sql[:-1]
    execute_raw_sql(sql, alias='default')


def execute_summary_sql(sql, alias='analytic', use_dict=True):
    conn = connections[alias]
    cur = conn.cursor()
    cur.execute(sql)
    if use_dict:
        return dict_fetchall(cur)
    else:
        return cur.fetchall()


def get_safe_sql_special_value(value):
    """防止sql注入(特别字符处理)"""
    value = re.sub(safe_sql_pattern, '', str(value))
    if "\\" in value:
        try:
            # \转义
            value_list = value.split("\\")
            value = '\\\\'.join(value_list)
        except Exception as e:
            pass

    return value



def md5_encrypt(content):
    """
    md5加密数据
    """

    return hashlib.md5(content.encode('utf-8')).hexdigest()

class SqlPagination(object):
    """使用原始 SQL 分页获取结果"""

    def __init__(self, sql, page_size, page_no):
        self.sql = sql
        self.md5_key = md5_encrypt(sql)
        self.cache_count = 0
        self.page_size = int(page_size)
        self.page_no = int(page_no)
        self.limit_str = ''
        self.count_db = 'analytic'  # 统计使用的db
        self.set_limit()

    def get_count_sql(self):
        return 'select count(0)  from (%s) newTable' % self.sql

    def _get_count(self):
        count_sql = self.get_count_sql()
        result = execute_raw_sql(count_sql, use_dict=False, alias=self.count_db)
        return result[0][0]

    @cached_property
    def count(self):
        self.cache_count = cache.get(self.md5_key)
        if self.cache_count is None:
            self.cache_count = self._get_count()
            cache.set(self.md5_key, self.cache_count, 60 * 10)
        return self.cache_count

    def get_query_sql(self):
        return '%s %s' % (self.sql, self.limit_str)

    def set_limit(self):
        """设置sql limit
        """
        self.limit_str = 'limit %s,%s' % ((self.page_no - 1) * self.page_size, self.page_size)

    def get_results(self, alias='default', use_dict=True, is_generator=False):
        query_sql = self.get_query_sql()
        return execute_raw_sql(query_sql, alias, use_dict, is_generator)


    @cached_property
    def num_pages(self):
        """Return the total number of pages."""
        if self.count == 0:
            return 0
        return ceil(self.count / self.page_size)


def q2where(q: Q, model_class: Model, replace_table='') -> str:
    """
    django 的 filter Q 转为 where 的 sql 条件
    @param q: django 的 filter Q
    @param model_class:  模型类
    @param replace_table: 替换 as xxx
    @return: str

    @example:
    from background_order.models import Order
    print(q2where(Q(name='"name" or id =3', id=3) | Q(id=4), Order))
    """
    query = Query(model_class)  # replace "MyModel" with your model
    compiler = SQLCompiler(query, connection, None)
    query_str, args = q.resolve_expression(query).as_sql(compiler, connection)
    if replace_table:
        query_str = query_str.replace(f'`{model_class._meta.db_table}`.',f'`{replace_table}`.')
    where_str = query_str % tuple(sv(v) for v in args)
    return f' {(where_str or "1=1")} '

def case_when(case_map, field_name, alias='', else_value=''):
    """
    根据字段生产 case when sql，方便写原生 sql 显示别名
    @param case_map:
    @param field_name:
    @param alias:
    @param else_value:
    @return: str

    @example:
    case_map = {"X": "X-ray", "Y": "Yard"}
    field_name = "letter"

    expected_sql = (
        "CASE \n"
        "        WHEN `letter` = 'X' THEN 'X-ray'\n"
        "        WHEN `letter` = 'Y' THEN 'Yard'\n"
        "END"
    )
    result = case_when(case_map, field_name)
    """

    case_lines = [
        f"        WHEN {connection.ops.quote_name(field_name)} = {sv(condition)} THEN {sv(result)}" if isinstance(condition, str)
        else f"        WHEN {connection.ops.quote_name(field_name)} = {condition} THEN {sv(result)}"
        for condition, result in case_map.items()
    ]
    case_statement = "\n".join(case_lines)
    else_clause = f"\n        ELSE {sv(else_value)}" if else_value else ''
    case_sql = f"CASE \n{case_statement}{else_clause}\nEND"
    if alias:
        case_sql += f" AS {alias}"
    return case_sql.strip()

