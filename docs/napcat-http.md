# NapCat HTTP 接入约定

本文说明本仓库扩展的接入方式。现有实现参考 [签到通知客户端](../extensions/uestc-checkin/app/notify.py) 和 [项目连接说明](../extensions/uestc-checkin/NAPCAT_SETUP.md)。NapCat 具体支持的动作及字段以实际部署版本的接口为准。

## 连接关系

```text
AstrBot <-- OneBot 反向 WebSocket -- NapCat <-- QQ
                                      ^
                                      | OneBot HTTP 动作调用
                        extensions/<name> 独立应用
```

AstrBot 继续使用已有 WebSocket 连接；扩展通过 NapCat 的 HTTP 服务端调用动作。HTTP 扩展不需要再启动一份 QQ 客户端。6099 是 NapCat WebUI 管理端口，不能填作消息 API 地址。

主动调用 HTTP API 与接收消息事件是两条链路。当前签到扩展只主动发送通知，没有事件接收服务。将来若扩展需要监听 QQ 消息，应单独设计事件入口、NapCat 事件投递配置、来源校验与事件去重，并明确它和 AstrBot 的响应分工；仅配置 `NAPCAT_HTTP_URL` 不会自动收到消息。

## 配置与网络

| 字段 | 含义 |
| --- | --- |
| `NAPCAT_HTTP_URL` | OneBot HTTP 服务根地址，不包含动作路径 |
| `NAPCAT_TOKEN` | 对应 HTTP 服务的访问 Token，与 WebUI 凭证分开 |
| `QQ_USER_ID` | 需要私聊通知时配置的收件人；其他目标由扩展自行定义 |
| `BOT_NETWORK` | 使用网络覆盖配置时，已有 Docker 网络的实际名称 |

生产扩展通过外部 Docker 网络连接 NapCat。根目录 Compose 项目名为 `qq-bot`，网络键为 `bot`，默认网络名为 `qq-bot_bot`；实际部署改过项目名时应核实。通过该网络访问 NapCat 服务别名 `napcat`，端口填写实际启用的 OneBot HTTP 监听端口。例如启用 3000 时可使用 `http://napcat:3000`。现有签到项目也保留了云端容器名地址的部署记录。

扩展 Compose 的可选覆盖配置可参考：

```yaml
services:
  worker: # 替换为当前扩展需要访问 NapCat 的服务名
    networks: [default, bot]

networks:
  bot:
    external: true
    name: ${BOT_NETWORK:?Set BOT_NETWORK to the existing robot network}
```

此片段只描述网络，需与扩展自身的 Compose 文件合并使用。已有签到项目的 `cli` 和 `scheduler` 配置见 [compose.napcat.yaml](../extensions/uestc-checkin/compose.napcat.yaml)。

HTTP 服务应按需在 NapCat 中启用，配置 Token 并监听容器内可达地址；根目录 Compose 当前只映射 WebUI 端口，没有映射 HTTP API。共用 Docker 网络无需新增宿主机端口。Mac 本地调试如需访问云端，可按项目说明使用 SSH 隧道；不要把生产 API 直接暴露到公网。

## 请求、结果和重试

现有通知客户端向 `<NAPCAT_HTTP_URL>/send_private_msg` 发送 JSON，使用 `Authorization: Bearer <NAPCAT_TOKEN>`。消息采用 OneBot 消息段数组，文本段包含 `type: text` 和 `data.text`；目标使用 `user_id`。

客户端应同时检查 HTTP 请求结果和 OneBot 业务响应。现有实现要求 `status == "ok"`、`retcode == 0` 且返回 `data.message_id`，才将消息标记为接口已接收。这不能证明用户已经阅读。

请求设定有限超时，避免把 Token 传给重定向目标或无关代理，日志只记录必要的状态和脱敏错误。业务任务结果与通知结果分开落盘；通知失败后只补发通知，不重复执行业务操作。

超时存在“消息已发送但响应丢失”的可能。为通知队列设置业务去重键、有限批量和重试节奏，并在项目说明中写明重复投递边界。当前签到扩展按当日状态去重，但网络响应丢失后的补发仍可能重复，不保证恰好一次送达。

## 验证方式

先用模拟 HTTP 服务验证鉴权头、请求体、业务失败、超时和队列恢复，再进行部署配置检查。实际机器人联调时先检查在线状态；真实发消息作为单独明确的操作，不能混入默认测试或普通配置检查。仓库整理不会自动启用 HTTP 服务或修改线上 NapCat 配置。
