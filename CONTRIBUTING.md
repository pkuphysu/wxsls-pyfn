## 如何开发

### Commit Style?

最好是 [Angular's conventional commit](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)，但是不做强制要求。

### Commit 失败？

如果是代码的问题，建议对应信息检查后修复。

如果是 pre-commit 无法跑起来，检查 `.git/hooks/pre-commit` 的配置，尤其是 `INSTALL_PYTHON` 项。

### 如何开发短期业务？

在 `api` 下新建文件夹，模仿已有的功能写好业务代码。

然后修改 `api/__init__.py`，在 `modules` 中加上新建的模块名称。

功能使命结束，则将 `modules` 回复原样即可。

### 如何使用参数？

对于不敏感的参数，直接在 `config/settings.toml` 下新建一块 `[default.name]`，然后直接用 `settings.name.CONFIG_NAME` 调用即可。

### 新建了数据库表的 Model，怎么 create?

分两种情况。如果是刚刚建立，那么管理员的微信授权还不能完成，则应该使用 `/tasks/db/create?token=<TASK_AUTH_TOKEN>` 完成数据库表的初始创建。

如果是后期维护，则使用 `wxsls-pages` 配套的 admin 页面，即 `/dba/*` 接口完成创建。

### API Feel

尽量使用 RESTful 的 convention（虽然这不太可能）。

应该使用 `utils.respond_error` 和 `utils.respond_success` 返回错误和成功，以保证 API 的一致性。
