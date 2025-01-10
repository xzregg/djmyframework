# -*- coding: utf-8 -*-
# @Time    : 2024/12/11 10:37 
# @Author  : xzr
# @File    : test_sql.py
# @Software: PyCharm
# @Contact : xzregg@gmail.com
# @Desc    :


import unittest
from ..utils.sql import case_when,q2where,Q
import unittest

class TestCaseWhen(unittest.TestCase):
    def test_basic_case_when(self):
        case_map = {"A": "Apple", "B": "Banana"}
        field_name = "fruit_code"
        alias = "fruit_name"
        else_value = "Unknown"

        expected_sql = (
            "CASE \n"
            "        WHEN `fruit_code` = 'A' THEN 'Apple'\n"
            "        WHEN `fruit_code` = 'B' THEN 'Banana'\n"
            "        ELSE 'Unknown'\n"
            "END AS `fruit_name`"
        )

        result = case_when(case_map, field_name, alias, else_value)
        self.assertEqual(result.strip(), expected_sql.strip())

    def test_case_when_without_else(self):
        case_map = {1: "One", 2: "Two"}
        field_name = "number"
        alias = "number_name"

        expected_sql = (
            "CASE \n"
            "        WHEN `number` = 1 THEN 'One'\n"
            "        WHEN `number` = 2 THEN 'Two'\n"
            "END AS `number_name`"
        )

        result = case_when(case_map, field_name, alias)
        self.assertEqual(result.strip(), expected_sql.strip())

    def test_case_when_no_alias_or_else(self):
        case_map = {"X": "X-ray", "Y": "Yard"}
        field_name = "letter"

        expected_sql = (
            "CASE \n"
            "        WHEN `letter` = 'X' THEN 'X-ray'\n"
            "        WHEN `letter` = 'Y' THEN 'Yard'\n"
            "END"
        )

        result = case_when(case_map, field_name)
        self.assertEqual(result.strip(), expected_sql.strip())

    def test_q2where(self):
        from background_order.models import Order
        print(q2where(Q(name='"name" or id =3', id=3) | Q(id=4), Order))
        print(q2where(Q(name__icontains='"name" or id =3', id=3) | Q(id=4), Order,'o'))
        print(q2where(Q(), Order))


if __name__ == "__main__":
    unittest.main()

