
[![PyPI version](https://badge.fury.io/py/djmyframework.svg)](https://badge.fury.io/py/djmyframework)

## 通用后台框架 3.7

### 特性
 - 在settings 配置INSTALL_APPS即可.
 - 无需配置urls,文件,约定大于配置.
 - 功能按apps目录分离.
 - 前后端分离,后端只返回json
 - 快速生成CURD模型
 - 多国语言
   - python manage.py makemessages  -i venv -l en
   - python manage.py  compilemessages -l en
   > 不要使用 django-admin ，会把 venv 带进去
 - 支持OpenApi 自动生成文档,客户端
  - python manage.py generate_swagger -f json -o static/api.json
  - 使用 idea OpenAPI Generator 插件生成客户端,On an OpenAPI Definition JSON or YAML file: Code -> OpenAPI -> Generate from document
 - 使用 jinja2 模板引擎

 
 
#### 放弃rest ,不适合业务
 - status_code 不够使用
 - 地址/xx/{id} 形式,容易产生缓存,不容易测试,批量删除与修改不方便
 - rest_framework 默认是使用csrf_exempt
 - 只使用 post ,get 方法
 
### 设置apps目录 
```bash
pycharm -> project structure -> 设置apps目录为source
``` 
 
 
### 新建表结构
```bash
python3 manage.py migrate 
```

## 前端使用库
 - jquery https://jquery.com/
 - 表单 jquery.form http://malsup.com/jquery/form/
 - ui 框架 bootstrap-3 https://v3.bootcss.com/
 - Bootstrap Tags Input http://bootstrap-tagsinput.github.io/bootstrap-tagsinput/examples/
 - 弹出框 dialog http://demo.jb51.net/js/2011/artDialog/_doc/API.html
 - 表格 bootstrap-table https://examples.bootstrap-table.com/index.html?bootstrap3#view-source 
 - 选择框 select2 https://select2.org/
 - 日期框 daterangepicker https://www.daterangepicker.cn/
 - progress.js https://usablica.github.io/progress.js/
 - vue 2.6 https://vuejs.org/
 - ant design vue https://www.antdv.com/docs/vue/introduce-cn/


## redoc
 - 使用 swagger_auto_schema 添加注释文档
 - query_serializer 查询参数 get/post 使用
 - request_body 请求主体 post 用
 - responses 返回
 - 生成 json/yaml 文件
```
    python manage.py generate_swagger -f yaml - >static/yaml.json
```
 - OpenAPI Generator 自动生成客户端文件 pycharm 插件 code -> OpenApi 
 
### 需要解决
 - 统一用 swagger_auto_schema 添加api文档注释,并且增加参数校验
   - 侵入度低,使用 __annotations__ 辅助
  
 - 返回response 统一带 code 参数有,需要统一增加,返回错误代码,也许动态增加,建议不使用动态生成rsp
 - 请求 body ,query, 需要添加filter,page_size 参数
 
## 快速上手 开发流程
#### 创建 app
 1.  与 django 命令相同,不过默认使用 framework 下的 app 模板
```bash
pip3 install djmyframework
mkdir xxxProject
cd xxxProject
djmyframework_init 
python3 manage.py create_app xxxApp
python3 manage.py migrate
python3 manage.py create_root
python3 manage.py create_role
python3 manage.py create_menu -m config.system_menu

```

#### 创建增删改查
 1. 定义好 models 后, 执行自动创建 view,template 模板
 ```bash
python3  manage.py create_curd {app_name}.{Model}
```

#### 部署
 1. 静态文件部署
 ```
 python manage.py collectstatic
 ```
 
 #### 启动服务
   参看 supervisorctl 用法
 ```
 mysupervisorctl start
 ```