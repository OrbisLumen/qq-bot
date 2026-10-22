# 独立扩展

这里放独立运行、通过 NapCat OneBot HTTP API 与 QQ 交互的应用。扩展拥有自己的配置、依赖、测试和生命周期；根目录机器人服务提供已有 QQ 连接。需要使用 AstrBot 的消息钩子、上下文或模型能力时，在 [plugins/](../plugins/README.md) 中编写插件。

| 扩展 | 功能 | 接入 | 部署 |
| --- | --- | --- | --- |
| [uestc-checkin](uestc-checkin/README.md) | 学校签到、状态复查与 QQ 私聊通知 | 主动调用 OneBot HTTP API | [独立 Docker Compose](uestc-checkin/DEPLOYMENT.md) |

## 新增扩展

使用 `extensions/<name>/`，名称采用小写单词和连字符。按项目实际需要创建以下内容；不用提前建立空目录：

```text
extensions/<name>/
├── README.md              # 用途、配置、运行命令和验证方法
├── .env.example           # 配置字段与非敏感默认值
├── .gitignore             # 项目特有的运行产物
├── .dockerignore          # 排除凭证、状态、缓存和备份
├── compose.yaml           # 独立项目名、资源限制和数据卷
├── compose.napcat.yaml    # 可选：加入已有机器人网络
├── Dockerfile
├── app/                   # 或对应语言的源码目录
├── tests/
└── DEPLOYMENT.md           # 部署、升级、停止、备份和恢复
```

每个扩展的 README 应说明：工作目录、入口命令、是否自动发消息或执行外部操作、配置字段、手动触发和调度方式、持久状态、失败恢复，以及测试是否访问真实服务。新增后在本页登记。

## 配置与部署约定

- 每个扩展使用本目录的 `.env`；根目录 `.env` 只配置机器人部署。HTTP 接入统一使用 `NAPCAT_HTTP_URL` 和 `NAPCAT_TOKEN`，需要私聊目标时使用 `QQ_USER_ID`。
- 在 `.env.example` 中留空凭证和个人信息。默认关闭自动调度和会产生业务副作用的操作；通过明确命令或配置启用。
- 每个扩展拥有唯一 Compose 项目名和自己的数据卷。命令与脚本从自身目录解析路径，支持仓库路径含空格。
- 通过可选覆盖配置加入已有 Docker 网络，不在扩展 Compose 中重复创建 NapCat。停止、升级扩展应能独立执行。
- 源码部署与运行状态分开管理。容器构建上下文仅限当前扩展目录，`.dockerignore` 排除本地凭证和状态；数据卷与 `.env` 分别备份。
- HTTP 调用要有超时和业务响应检查。重试与去重按具体业务设计；参考 [HTTP 接入约定](../docs/napcat-http.md)。当前客户端实现位于各扩展内部，出现多个实际复用者后再考虑公共库。

## 合入前检查

1. 检查暂存内容，确认不含 `.env`、会话、真实收件人、定位、Token 或备份。
2. 从扩展目录验证配置能解析，执行项目测试；消息接口使用模拟服务，真实发送应由明确操作触发。
3. 核对独立启动、停止和升级命令，以及数据保留、通知失败和任务重启后的行为。
4. 更新本页索引、项目 README 和对应部署说明，记录未完成的验证。

目录调整历史：`uestc-checkin/` 已移到 `extensions/uestc-checkin/`，本地 `.env` 等忽略文件随目录保留。原有云端安装路径与命名卷保持不变，详见其部署说明。
