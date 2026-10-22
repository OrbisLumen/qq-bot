# 复用云端 NapCat

生产部署使用 `BOT_NETWORK=qq-bot_bot` 和 `NAPCAT_HTTP_URL=http://qq-bot-napcat-1:3000`，通过 `scripts/cloud.sh` 将签到容器连接到已有 Docker 网络。无需本地隧道、额外 QQ 登录或重启机器人。下述 SSH 隧道仅保留为本地调试说明；迁移验收时已关闭此前的本地专用隧道。

2026-10-21 经用户明确授权，已通过 NapCat v4.18.37 WebUI 接口在线新增 `uestc-checkin` HTTP 服务（容器内 0.0.0.0:3000）。鉴权、QQ 在线状态和 AstrBot TCP 连接验证通过；两个容器的启动时间、PID 和重启次数均未变化，未开放公网端口。

本地不需要启动 NapCat 或 AstrBot。接收 QQ 已写入本项目 `.env`，并生成独立的 `NAPCAT_TOKEN`。消息 API 地址为 `http://host.docker.internal:13000`，通过 SSH 隧道连接云端。已验证本地 Docker 可访问 API，且项目 NotificationManager 的真实私聊测试返回成功。消息提交成功不等于客户端已读。

## 1. 服务器 NapCat 配置

在已有 NapCat WebUI 的网络配置里新增 **HTTP 服务端**：

| 字段 | 值 |
| --- | --- |
| 名称 | uestc-checkin |
| 启用 | 是 |
| 监听地址 | 0.0.0.0（NapCat 容器内） |
| 端口 | 3000（已启用，仅 Docker 内网） |
| Token | 专用 `.env` 中的 NAPCAT_TOKEN 值 |
| 消息格式 | array |

保留已有 AstrBot 反向 WebSocket 配置。此处使用的是 OneBot API Token，不能用 WebUI 登录 Token 替代。

不需要为 3000 增加 Docker 公网端口映射或云安全组规则。优先通过 WebUI 保存并启用新增服务，确认 AstrBot 原连接仍正常；本项目不会自动重启机器人。

## 2. 本地 SSH 隧道

服务器当前 NapCat 容器在 `qq-bot_bot` 网络中的 IP 是 `172.18.0.3`。该地址可能在容器重建后变化，届时应重新核实。

需要本地调试时可重新建立隧道。在本机终端运行（使用已提供的密钥，替换 SSH 目标）：

```bash
ssh -i ~/.ssh/mac.pem -N -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:13000:172.18.0.3:3000 \
  -L 127.0.0.1:16099:127.0.0.1:6099 ubuntu@你的服务器
```

隧道建立后，管理页面可通过 `http://127.0.0.1:16099/webui` 访问；使用服务器上现有的 WebUI 登录凭证。16099 仅供本地管理，和程序使用的 API 端口 13000 不同。

SSH 密码仅在终端输入，不写入项目配置或聊天。已有 SSH 会话可以继续保留；这条命令建立一条独立隧道。隧道通过本机回环端口转发，容器再经 Docker Desktop 的 `host.docker.internal` 访问。

## 3. 验证顺序

1. 验证 SSH 隧道和 OneBot `get_status`，以及机器人是否在线。
2. 发送一条明确标为“联调测试”的 QQ 私聊消息。
3. 单独验证学校登录及签到页面状态。
4. 在页面开放且业务条件确认后，再执行签到与通知的完整验收。

通知失败时只补发通知，不重复签到。云端迁移后改用同一 Docker 网络中的 NapCat API 地址，取消本地 SSH 隧道。

## 已完成的服务器变更与恢复资料

- 仅新增名为 `uestc-checkin` 的 HTTP 服务；已有网络配置逐项比对保持一致。
- 已验证无 Token 请求被拒绝。
- 从服务器直接发送一条联调消息，再从本地 Docker 发送一条链路测试消息，两次均获得 message_id；未执行签到。
- 变更前配置及核对记录保存在服务器 `/var/backups/uestc-checkin/20261021-dd6fe4/`，目录和文件仅 root 可访问。
- 如需撤销，优先在 NapCat WebUI 中停用或删除这一项服务，不重启整个容器。
- 本地隧道存在时，可用 `ssh -S /tmp/uestc-checkin-ssh-bridge/control -O check ubuntu@你的服务器` 检查；停止用 `-O exit`，只影响该隧道。

当前专用隧道通过密钥登录，使用 `ControlPersist=yes`，不再采用此前 600 秒闲置退出设置。该隧道是本地开发所需的 SSH 基础连接；应用、测试和浏览器仍全部在 Docker 内运行。Mac 休眠、断网或关闭隧道后，本地消息发送会暂存 JSON 队列；恢复连接后补发。
