# CAS (Central Authentication Service)

采用 [django-cas-ng](https://pypi.org/project/django-cas-ng/) 向[学校的 CAS 服务器](https://login.bit.edu.cn/devcas/)认证，Django 服务器作 CAS 客户端。（参考 [django-cas-ng Example Project](https://djangocas.dev/blog/django-cas-ng-example-project/) 开头的图）

## 登录流程

1. 使用者访问登录页面，Django 服务器将请求转至 CAS 服务器。
2. 使用者填写 CAS 服务器的表单，CAS 服务器验证后返回 Django 服务器。
3. Django 服务器验证信息。若未见过，则在数据库中新建`User`、`Student`。
4. Django 服务器向使用者展示后续页面。

## 个人信息

学校的正式 CAS 服务器会将姓名存储到`userName`。

经过`settings.py`中`CAS_RENAME_ATTRIBUTES`规定的重命名，Django 中`User`的`username`是学号，`last_name`是姓名（不保证唯一），`first_name`空。

`Student`的`name`目前仍是学号，原本设计的是姓名。

## 版本问题

学校的 CAS 服务器可能是 2.0。Django 侧若用 3.0，会从 CAS 服务器接收到不合法的 HTML，导致无法正常登录。

## 可能遇到的错误

### 重定向次数过多

推测原因：接入 CAS 前后数据模型不同，接入前登录的账户也许无效了。

解决方法：访问`/accounts/logout/`以手动登出，再重试。
