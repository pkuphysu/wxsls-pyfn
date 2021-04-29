# 北京大学物院学生会微信公众号后台（回复核心）

使用腾讯云的 Serverless Framework. See Also:

- [wxsls-page](https://github.com/pkuphysu/wxsls-page) 零碎网页
- [wxsls-base](https://github.com/pkuphysu/wxsls-base) 基本组件

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
[default]
TASK_AUTH_TOKEN = "liyanjieqing"

[default.flask]
dynaconf_merge = true
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://user:password@localhost/wechat"

[default.wechat]
APP_ID = ""
APP_SECRET = ""
TOKEN = "token"
MASTER_IDS = ["<your open id>"]
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

本地运行时可使用 `developmentoken` 作为 token，绕过微信授权。

### 发布

发布部分逻辑已写进 GitHub Actions

## TODO

- [ ] 定时任务的实现（类似 web-cron）
- [ ] 对活动代码的集成（等有活动了再说）
- [X] 一键部署的方案
- [X] （管理向）腾讯云集体账号管理
