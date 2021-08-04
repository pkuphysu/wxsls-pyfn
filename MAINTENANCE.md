## 维护

### 更改配置文件（以新增管理员为例）

众所周知，该项目的管理员列表是通过配置文件手动维护的。（当然如果做了相关的数据库功能更好。）最频繁的修改配置文件的操作莫过于新增/删除管理员了。

管理员列表的配置文件属于 secret，通过 GitHub Actions 的 secrets 功能来完成部署。当 `secrets.toml` 更改时，应当按照 `/scripts/secret_encoder.py` 的指示生成 base64 并更新 GitHub Actions 的 secrets。

但是更新了 GitHub Actions 的 secrets 并不代表腾讯云上的配置文件倍更改。要应用到腾讯云上有两种方法：
1. 手动修改腾讯云函数上的配置文件
2. 提交 commit 触发 CI

如果没什么好 commit 的，那就上腾讯云后台改吧。
