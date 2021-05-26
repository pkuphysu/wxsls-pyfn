# 如何开发

注：所讲并非绝对，如有变动请及时修改。

## 代码管理

### Code Style

**注意** ❗ 在写代码之前，强烈建议阅读 [clean-code-python](https://github.com/zedr/clean-code-python) 或类似指导。始终记住，代码写出来不止你一个人看。

### API Feel

尽量使用 RESTful 的 convention（虽然这不太可能）。

应该使用 `utils.respond_error` 和 `utils.respond_success` 返回错误和成功，以保证 API 的一致性。

### 文件命名

按照习惯，一个模块内，所有的路由放在 `views.py` 内，所有 SQLAlchemy 的 model definition 都放在 `models.py` 内。

### 参数或常量

对于不敏感的参数，直接在 `config/settings.toml` 下新建一块 `[default.name]`，然后直接用 `settings.name.CONFIG_NAME` 调用即可。

如果涉及敏感信息，应该写入 `config/.secrets.local.yaml`。该文件可从云函数后台代码获取，修改后根据 `scripts/secret_encoder.py` 完成部署。

## Commit

### Commit Message Style

最好是 [Angular's conventional commit](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)，但是不做强制要求。

但是必须避免废话式的提交信息，比如 `fix some bugs`, `enhance`。还是那句活，几个月后看到[满屏都是 `bug fix`](https://github.com/treehollow/treehollow-backend/commits/master) 怎么知道哪个是哪个？

### Commit 失败？

如果是使用 GUI 提交，请务必查看相应的 log

如果是代码的问题，建议对应信息检查后修复。

如果是 pre-commit 无法跑起来，检查 `.git/hooks/pre-commit` 的配置，尤其是 `INSTALL_PYTHON` 项。

## 功能性模块的工作流

功能性模块与基础性模块相区别。基础性模块是每项活动都会用到的模块，比如用户管理、数据库管理等；功能性模块是具体活动功能的实现。

约定功能性的模块均放在 `api` 下，由 `api/__init__.py` 控制是否 import 该模块。

工作流大致如下：

1. 从 master 新建一个分支
2. 在 `api` 下新建文件夹，模仿已有的功能写好业务代码。然后修改 `api/__init__.py`，在 `modules` 中加上新建的模块名称。
3. 在 `tests/api/<模块名称>` 下新建测试文件，完成基本的 API 测试。
4. 如可以，在本地开启前端后端进行联合调试
5. 【如有在线全真调试需求】从 master 新建 dev 分支
6. 【如有在线全真调试需求】合并进 dev，调试 dev，汇总问题并修改
7. 从 dev 或新建的分支向 master 发起 PR
8. review 通过后，根据 commit 是否混乱，决定是 create merge commit 还是 squash merge
9. 该新建分支与 dev 分支的历史使命已经结束，删除以保持整洁
10. 如果上线后有问题，可以视时间紧迫与代码修改方便程度，选择直接在腾讯云在线修改代码还是重复以上步骤
11. 功能使命结束，在 dev 上则将 `modules` 回复原样即可，适时如上 merge into master

## 数据库管理

在本地开发中，最常见的是在数据库中没有一张对应的表。那么管理员的微信授权还不能完成，则应该使用 `/tasks/db/create?token=<TASK_AUTH_TOKEN>` 完成数据库表的初始创建。

在维护中，最常见的情况是新建了 SQLAlchemy 的 Model，在数据库中创建对应的表。这时可以使用 `wxsls-pages` 配套的 admin 页面，即 `/dba/*` 接口完成创建。该接口还有上传数据、清空数据表、migrate 数据表的功能，在维护中会很有用。
