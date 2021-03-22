# 北京大学物院学生会微信公众号后台（回复核心）

使用腾讯云的云开发（cloudbase）加 PostgreSQL ServerlessDB

## 为什么不……

### 直接用云服务器？

学生机必然要每年迁移，每年迁移比较麻烦。

直接不靠优惠购买太贵了。

### 用云开发提供的数据库？

没有 Python SDK 啊

## 本地开发和部署

### 安装 [poetry](https://github.com/python-poetry/poetry) 并安装依赖

不必赘述

### 安装 [pre-commit](https://github.com/pre-commit/pre-commit) 的 hook

```sh
poetry run pre-commit install
```

### 安装并初始化 PostgreSQL 数据库

```sql
CREATE DATABASE wechat WITH ENCODING 'UTF8'
```

### 设置文件 `.secret.local.toml`

本项目使用 [Dynaconf](https://github.com/rochacbruno/dynaconf)

参考以下模板，基本与 `settings.toml` 一致

```toml
[default.flask]
dynaconf_merge = true
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://user:password@localhost/wechat"

[default.wechat]
APP_ID = ""
APP_SECRET = ""
TOKEN = "token"
MASTER_IDS = ["<your open id>"]
```


### `releaser` 脚本的使用

打包代码，用于上传至云函数代码
```sh
poetry run releaser -c
```
打包依赖库，用于上传至云函数的层。注意必须在 3.6 的 Linux 环境中进行，以保证和云端环境一致。
```sh
poetry run releaser -d
```
打包代码和依赖库，用于上传至云函数代码（包含依赖库的方案）
```sh
poetry run releaser -cd
```

### 本地运行

可以跑测试

```sh
poetry run pytest
```

可以开本地服务器 + Tunnel Service 和测试号连接

```sh
poetry run flask run
ngrok http 5000
```


## TODO

- [ ] 定时任务的实现（类似 web-cron）
- [ ] 对活动代码的集成（等有活动了再说）
- [ ] 一键部署的方案（研究一下 `@cloudbase/cli` 的实现方式）
- [ ] （管理向）腾讯云集体账号管理
