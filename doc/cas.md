# CAS (Central Authentication Service)

采用 [django-cas-ng](https://pypi.org/project/django-cas-ng/) 向[学校的 CAS 服务器](https://login.bit.edu.cn/devcas/)认证，Django 服务器作 CAS 客户端。（参考 [django-cas-ng Example Project](https://djangocas.dev/blog/django-cas-ng-example-project/) 开头的图）

## 登录流程

1. 使用者访问登录页面，Django 服务器将请求转至 CAS 服务器。
2. 使用者填写 CAS 服务器的表单，CAS 服务器验证后返回 Django 服务器。
3. Django 服务器验证信息。若未见过，则在数据库中新建`User`、`Student`。
4. Django 服务器向使用者展示后续页面。

## 版本问题

学校的 CAS 服务器可能是 2.0。Django 侧若用 3.0，会从 CAS 服务器接收到不合法的 HTML，导致无法正常登录。
