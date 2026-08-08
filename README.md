# 北京大学物院学生会微信公众号后台（回复核心）

使用腾讯云的 Serverless Framework. See Also:

- [wxsls-page](https://github.com/pkuphysu/wxsls-page) 零碎网页
- [wxsls-base](https://github.com/pkuphysu/wxsls-base) 基本组件

## 为什么不……

### 直接用云服务器？

学生机必然要每年迁移，每年迁移比较麻烦。

直接不靠优惠购买太贵了。网络、性能的弹性也很难满足需求。

### 用云开发系列？

它的数据库没有 Python SDK 啊

## 本地开发和部署

更多开发约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### Python 和 Poetry 环境

项目要求 Python `^3.6.1`，CI 使用 Python 3.6 和 Poetry 1.1.6。Python 3.6
已经停止维护，不建议安装到系统环境中；应使用项目内的 Conda/virtualenv 前缀或
容器隔离。

当前开发环境采用以下项目内布局，两个目录均已加入 `.gitignore`：

- `.venv/`：Python 3.6 和项目依赖；
- `.poetry/`：由系统 Python 3.9 驱动的 Poetry 1.1.6，避免 Poetry 自身依赖污染
  项目环境。

环境创建完成后，安装依赖并配置提交检查：

```sh
source .venv/bin/activate
python --version       # Python 3.6.x
poetry --version       # Poetry 1.1.6
poetry install
poetry run pre-commit install
```

依赖以 `poetry.lock` 为准，包源使用官方 PyPI。不要使用系统 `pip` 安装项目依赖。

### 启动并初始化 MySQL 8.4 LTS 数据库

本地开发使用仓库中的 Compose 配置，数据库数据保存在独立 volume 中：

```sh
docker compose up -d mysql
docker compose ps mysql
```

默认仅监听本机 `127.0.0.1:3306`，开发数据库、用户和密码分别为
`wechat`、`user` 和 `password`，默认字符集为 `utf8mb4`。

当前已配置过的 Podman 开发机可以直接管理现有容器：

```sh
podman start wxsls-mysql
podman ps --filter name=wxsls-mysql
podman logs -f wxsls-mysql
podman stop wxsls-mysql
```

`docker compose down` 只停止并删除容器，不会删除数据库 volume；只有明确需要清空
本地数据库时才使用 `docker compose down -v`。

### 配置本地密钥

本项目使用 [Dynaconf](https://github.com/rochacbruno/dynaconf)。本地配置文件的实际
路径为 `src/pkuphysu_wechat/config/.secrets.toml`，该文件包含敏感信息，不应提交到
版本库。

可以从以下模板开始：

```toml
[default]
TASK_AUTH_TOKEN = "liyanjieqing"

[default.flask]
dynaconf_merge = true
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:password@127.0.0.1:3306/wechat?charset=utf8mb4"

[default.wechat]
APP_ID = ""
APP_SECRET = ""
TOKEN = "token"
MASTER_IDS = ["<your open id>"]
```

### 本地运行

运行测试：

```sh
poetry run pytest
```

启动 Flask 开发服务器时需要从 `src/` 目录读取 `.flaskenv`：

```sh
cd src
poetry run flask run
```

首次启动后，通过任务接口创建数据库表：

```sh
curl "http://127.0.0.1:5000/tasks/db/create?token=<TASK_AUTH_TOKEN>"
```

如需连接微信测试号，可以另开终端启动 Tunnel Service：

```sh
ngrok http 5000
```

本地运行时可使用 `developmentoken` 作为 token，绕过微信授权。

### 发布

发布逻辑已写入 GitHub Actions。`dev` 分支会发布到 dev 环境，`master` 分支会发布到
prod 环境；部署连接同样使用 `mysql+pymysql`。

### 触发

大多数触发已在前端配置；如需人工触发，可在腾讯云触发管理中查看对应 URL。

## TODO

- [ ] 定时任务的实现（类似 web-cron）
- [ ] 抽奖部分的整改
- [X] 对活动代码的集成（等有活动了再说）
- [X] 一键部署的方案
- [X] （管理向）腾讯云集体账号管理
