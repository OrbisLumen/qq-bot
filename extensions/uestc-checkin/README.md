# uestc-checkin

本项目位于仓库的 `extensions/uestc-checkin/`，是独立运行的 NapCat HTTP 扩展。仓库根目录下先执行 `cd extensions/uestc-checkin`，再运行本文命令。通用接入约定见 [NapCat HTTP 接入](../../docs/napcat-http.md)。

Python + Playwright 容器内 Chromium + 内置 Geolocation + JSON 状态 + NapCat OneBot 私聊通知。开发、测试、登录和调度均由 Docker 执行，不使用本机 Python 或 Chrome 运行项目。生产目标为腾讯云独立执行，部署和运维见 [DEPLOYMENT.md](DEPLOYMENT.md)。


## 当前真实联调状态（2026-10-21）

- 学校账号已在容器浏览器中人工登录；无头容器恢复会话验证成功。登录成功后调试入口会自动关闭，这是正常行为。
- 本地专用 `.env` 已使用 `CHECKIN_ADAPTER=uestc`，入口为已验证的“晚安成电”卡片。适配器被动读取正常页面发出的今日记录和时间配置 GET 响应，不复制认证请求，不直接构造签到 POST。
- 本地 Docker 已完成真实签到，学校后台时间为 `2026-10-21T21:09:15+08:00`，新容器复查一致。确认成功要求业务状态 `CHECKED_IN`、今日业务日期与有效签到时间同时匹配；免签到、已填报情况和异常记录分别处理。
- 定位按系统分配的允许区域中心配置。学校前端会将 WGS84 转为 GCJ-02，专用 `.env` 保存对应 WGS84 输入。本次真实提交已被服务端接受，未来平台校验变化仍可能需要人工处理。
- 云端 NapCat 内部 HTTP API 已授权启用，真实 QQ 通知通过。云端签到容器加入已有机器人网络后直接调用；本地调试才使用 SSH 隧道。参见 [NapCat 连接说明](NAPCAT_SETUP.md)。
- 本地配置保持自动提交关闭；云端生产配置启用提交和每日 21:05 调度。实际部署验收记录见 [VALIDATION.md](VALIDATION.md)。

本地检查使用 `docker compose run --rm cli status`，云端使用 `sudo ./scripts/cloud.sh run --rm cli status`；已发通知会按当日状态去重。

## 快速验证

在本目录执行。首次构建会下载包含 Chromium 的 Playwright 镜像。

```bash
(umask 077; cp -n .env.example .env)
chmod 600 .env
docker compose build cli
docker compose run --rm test
docker compose run --rm cli demo
```

`demo` 使用容器内真实 Chromium、拦截的模拟学校页面和容器内临时 OneBot HTTP 服务。它验证登录、定位坐标、模拟提交、刷新后复查、第二次执行跳过和单次通知；不会请求学校或发送真实 QQ 消息。演示数据临时创建并清理，不污染正式数据卷。

预期输出包含：`status: COMPLETED`、`geolocation: verified`、`submissions: 1`、`second_run: skipped`、`real_qq_messages: 0`。

## 配置与真实页面接入

通过编辑器填写本目录 `.env`。Compose 将变量注入容器，不将凭证打包到镜像。配置保持在被 Git 忽略的本地文件，勿粘贴凭证到聊天。密码含 `$` 等插值字符时，在 `.env` 中用单引号包住密码。

- `UESTC_USERNAME` / `UESTC_PASSWORD`：学校账号，允许留空后通过容器浏览器人工登录。
- `GEO_LATITUDE` / `GEO_LONGITUDE`：填写 WGS84 坐标，同时填写才覆盖浏览器定位，同时留空则不覆盖。`GEO_ACCURACY_METERS` 为精度。
- `CHECKIN_URL` 或 `CHECKIN_ENTRY_SELECTOR`：真实签到页面 URL，或者登录后首页上的入口。支持同页跳转与新标签页。
- `CHECKIN_FRAME_SELECTOR`：业务位于 iframe 时填写该 iframe 的选择器。
- `CHECKIN_ADAPTER`：`generic` 使用通用 DOM 选择器；`uestc` 使用当前学校 H5 响应格式，后者不要求以下三个 DOM 状态选择器。
- `CHECKIN_PENDING_SELECTOR` / `CHECKIN_COMPLETED_SELECTOR` / `CHECKIN_TIME_SELECTOR`：互斥的状态标记及**今日签到记录的时间**。不可使用可能匹配历史记录或普通成功提示的宽泛文本。
- `CHECKIN_NOT_STARTED_SELECTOR`：可选的未开放标记。
- `CHECKIN_SUBMIT_SELECTOR` / `CHECKIN_CONFIRM_SELECTOR`：提交按钮及可选 DOM 确认按钮。JS confirm/alert 默认不自动接受，须实测适配。
- `CHECKIN_ENABLED`：默认 `false`；只有设置为 `true` 且明确运行 `run` 或启用调度时才能提交。

登录选择器依据真实页面验证；**示例配置保持通用模式且业务选择器留空**；专用配置已接入 UESTC 的真实入口和查询格式。未配置或未识别的状态失败退出，不报告签到成功。本次会话已通过浏览器真实提交；不保证后续票据或认证规则不变。

## 容器内首次登录与调试

```bash
docker compose build debug
docker compose --profile debug up debug
```

打开 [容器浏览器调试入口](http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale)，操作的是 Docker 内部 Chromium。浏览器会进入学校登录页，可填写账号并处理验证码。成功识别登录后任务自动退出；最长 600 秒。该入口仅绑定本机回环地址，不对公网开放。仅按需使用 Xvfb/noVNC，无完整桌面环境。普通任务采用无头浏览器，不依赖调试服务。

登录与自动任务共享同一个专用 profile 和任务锁，不能并行打开。不要导入个人日常 Chrome profile。`AUTHENTICATED` 仅代表平台首页登录有效，不代表签到成功。

```bash
# 检查会话，不提交密码
docker compose run --rm cli check
# 会话失效时最多尝试一次密码登录
docker compose run --rm cli login
# 核查账号/验证码后解除自动认证暂停；此命令本身不登录
docker compose run --rm cli resume
# 只查询签到状态，不自动输入密码、不提交签到
docker compose run --rm cli status
# 明确执行一次登录、签到与复查，要求配置完整且 CHECKIN_ENABLED=true
docker compose run --rm cli run
```

`status` / `run` 在配置通知后会发送相应状态。普通 `check` / `login` 只输出结果，不发消息。若出现密码拒绝、验证码或无法确认认证结果，保留暂停标记，避免循环登录。

## NapCat 私聊通知

需启用 NapCat 的 **OneBot HTTP 服务端**，填写 `NAPCAT_HTTP_URL`、`NAPCAT_TOKEN` 和目标 `QQ_USER_ID`。6099 是 WebUI，不是消息 API。此项目不自动更改现有 NapCat 或 AstrBot 配置。

- NapCat API 已映射到 Mac 主机时，可使用 `http://host.docker.internal:<实际API端口>`。确认监听地址能被容器访问。
- 同一 Docker 网络内可使用 `http://napcat:<实际API端口>`，无需把 API 暴露到公网。提供可选网络覆盖文件，使用前核实实际网络名。

```bash
# .env 中额外设置 BOT_NETWORK=实际机器人网络名；并设置内部 NapCat URL
# 以下配置示例只连接已有网络，不修改机器人容器。
docker compose -f compose.yaml -f compose.napcat.yaml run --rm cli status
# 只补发 JSON 中的待发通知，不打开浏览器、不重新签到
docker compose run --rm cli flush-notifications
```

通知调用 `send_private_msg`，检查 OneBot 业务码和 message_id。失败保留待发记录，每次最多处理三条；调度器每 30 秒尝试补发。单次命令失败后可手动补发。消息接口已接收但响应丢失时，补发可能产生重复消息，不能保证恰好一次送达。

## 调度与状态

```bash
# 本地手动启动示例；云端请使用 scripts/cloud.sh
docker compose --profile scheduled up -d scheduler
docker compose logs -f scheduler
docker compose --profile scheduled stop scheduler
```

使用 `Asia/Shanghai`，默认 21:05，支持 `CHECKIN_HOUR` / `CHECKIN_MINUTE`。每天最多安排一次，在该小时内可补执行；过了该小时不自动补签。调度不自动重复密码认证或不确定的提交。重启后保留已安排日期。

命名卷 `uestc-checkin_checkin-data` 保存：

- `browser-profile/`：专用浏览器登录会话。
- `state.json`：每日结果、提交前标记、通知队列与调度日期。
- `auth-paused`、`task.lock`、`scheduler.lock`：认证暂停与单实例控制。

提交前落盘 `SUBMITTING`；异常或超时后当天保留未确认状态，不盲目再次提交。用 `status` 复查；确认已完成时会恢复为 `COMPLETED`。初版不提供自动清除未确认状态的命令。JSON 损坏时失败退出，不能当作空状态继续提交。

退出码：0 表示登录有效、成功识别业务状态或演示通过；2 表示需人工处理、未确认、业务运行失败，或仅补发命令仍有通知待发；3 表示任务整体超时/主进程错误；4 表示任务已被占用。签到成功但通知待发仍会报告签到成功，通知状态单独输出。

## Docker 隔离与迁移准备

独立 Compose 项目，不接管根目录 QQ Bot。使用非 root 用户、浏览器 sandbox、仅保留 SYS_CHROOT capability、官方 seccomp 配置（源自 Playwright v1.56.0）、init、日志轮转和任务硬超时。默认内存上限 768 MiB、CPU 1 核、共享内存 256 MiB；腾讯云 2GB 服务器的本次真实记录复查任务峰值约 325 MiB，未发生 OOM，峰值不代表所有未来页面负载。

迁移时复制源文件与专用 `.env`，并单独备份/恢复数据卷；镜像按目标 CPU 架构重新构建。浏览器版本保持一致，跨设备恢复后必须验证会话，不能承诺免重新认证。`docker compose down` 保留数据；`down -v` 会删除会话和状态，请勿作为常规重启操作。

参考：[Playwright 定位](https://playwright.dev/python/docs/emulation#geolocation)、[Docker 与 seccomp](https://playwright.dev/python/docs/docker)、[NapCat API](https://napneko.github.io/onebot/api)。

坐标准备参考：[wandergis/coordtransform](https://github.com/wandergis/coordtransform)。仅用于本次坐标准备与校验，不增加运行时扩展或依赖；浏览器定位始终由 Playwright 提供。
