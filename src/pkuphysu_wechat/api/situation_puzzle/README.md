# 海龟汤部分

百度获得其英语叫situation puzzle

## 要求

2022暑假加入海龟汤游戏，基于生活部给定的谜面，回答相应问题。细节的说明可以加一些。

## 流程

1. 玩家输入 `海龟汤 汤面`（或 `situation_puzzle 汤面`）查看当前谜面。
2. 玩家每轮输入 `海龟汤 <问题>`，由 AI 汤主根据隐藏汤底回答。
3. 玩家可以把完整推理直接发给 AI 汤主判断，也可以使用兼容命令
   `海龟汤回答 <完整推理>`。
4. 玩家输入 `海龟汤 重置` 开启新一局；旧记录仍保留在数据库，但不再进入模型上下文。
5. 玩家输入 `海龟汤 规则` 查看规则。

微信消息本身不使用内存会话。当前题号和每条 user/assistant 消息都存储在数据库，
每次模型调用前按 `open_id + puzzle_id` 重新加载最近的历史；完整历史仍保留在数据库。

## AI 配置

AI 调用兼容 OpenAI Chat Completions 协议，默认配置在
`config/settings.toml` 的 `[default.situation_puzzle_ai]`。密钥不得提交到仓库，使用
Dynaconf 环境变量或 `.secrets.toml` 配置，例如：

```sh
export DYNACONF_SITUATION_PUZZLE_AI__API_KEY="..."
export DYNACONF_SITUATION_PUZZLE_AI__MODEL="gpt-4o-mini"
```

如使用其他兼容服务，同时设置
`DYNACONF_SITUATION_PUZZLE_AI__API_URL`。部署前需要通过项目现有的建表/迁移接口创建
`SituationPuzzleState`、`SituationPuzzleConversation` 和 `SituationPuzzleTurn` 三张表。
生产环境也可以把密钥放入部署流程生成的 `.secrets.toml`。

系统提示词集中在 `prompts.py`，不会写入对话表。模型只能返回结构化 verdict；应用层
把 verdict 映射成“是 / 否 / 无关 / 无法确定”，并且只有 `solved` 才从服务端题库公布
汤底，模型生成的自由文本不会直接返回或持久化。

## 主要内容

### 数据库

题库保存在 `data/puzzle.json`。当前题号由 `SituationPuzzleState` 持久化，会话 generation
由 `SituationPuzzleConversation` 管理，每轮状态和内容由 `SituationPuzzleTurn` 以追加方式
持久化。旧的关键词依赖和固定选项回答不再参与游戏流程。
