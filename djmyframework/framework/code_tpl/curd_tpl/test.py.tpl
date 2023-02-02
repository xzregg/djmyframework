# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# @Time: ${datetime}
<%!
from django.db.models.fields import IntegerField,CharField,DateTimeField,BigAutoField,TextField,NOT_PROVIDED,BooleanField,FloatField,EmailField
from django.db.models.fields.related import ManyToManyField,ForeignKey,OneToOneField
from framework.models import BaseModelMixin
%>
from ${app_name}.models import *
from ${app_name}.serializer.${model_lower_name} import List${model_name}ReqSerializer, ${model_name}Serializer, IdsSerializer
from framework.tests import BaseTestCase
from tests.utils import get_auth_token_headers


class ${model_name}TestCase(BaseTestCase):
    """
    ${app_name} ${model_name} TestCase
    """

    def test_list(self):
        path = self.reverse('${app_name}.${model_lower_name}.list')
        headers = get_auth_token_headers('pushi')
        data = List${model_name}ReqSerializer().data
        response = self.post_json(path, data=data, **headers)
        result = response.josn()
        self.assertTrue(result['data'])

    def test_add(self):
        path = self.reverse('${app_name}.${model_lower_name}.add')
        data = ${model_name}Serializer().set_faker_data()
        data.id = None
        % for f in fields:
        % if isinstance(f,(CharField,)):
        #data.${f.name} = self.fk.name()
        % elif f.name!='id' and isinstance(f,(IntegerField,)):
        #data.${f.name} = 2
        % endif
        % endfor

        response = self.post_json(path, data=data, **get_auth_token_headers())
        result = response.json()
        #self.assertEqual(result['data']['name'], data.name)
        return result['data']

    def test_modify(self):
        path = self.reverse('${app_name}.${model_lower_name}.modify')
        data = ${model_name}Serializer().set_faker_data()
        data.id = self.test_add()['id']
        % for f in fields:
        % if isinstance(f,(CharField,)):
        #data.${f.name} = self.fk.name()
        % elif f.name!='id' and isinstance(f,(IntegerField,)):
        #data.${f.name} = 2
        % endif
        % endfor
        response = self.post_json(path, data, **get_auth_token_headers())
        result = response.json()
        #self.assertEqual(result['data']['name'], data.name)
        return result['data']

    def test_delete(self):
        path = self.reverse('${app_name}.${model_lower_name}.delete')
        data = IdsSerializer().set_faker_data()
        data.ids.append(self.test_add()['id'])
        response = self.post_json(path, data, **get_auth_token_headers())
        result = response.json()
        self.assertEqual(result['code'], 0)
        return result

