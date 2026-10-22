# 开发与 Git 管理

本仓库采用单仓库分目录管理。机器人部署位于根目录，AstrBot 进程内插件位于 `plugins/`，独立应用位于 `extensions/<name>/`。每个扩展保留自己的运行配置和依赖，不默认共用 Python 环境，也不建立嵌套 Git 仓库。上游源码仍遵循 `upstream/README.md` 的独立仓库约定。

## 改动范围

| 内容 | 位置 | 需要同步检查 |
| --- | --- | --- |
| 基础服务版本、端口、挂载 | 根目录 Compose、配置与脚本 | 根目录 README 和 Compose 解析 |
| AstrBot 插件 | `plugins/<name>/` | 挂载、插件说明与根目录 `tests/` |
| 独立 HTTP 扩展 | `extensions/<name>/` | 本项目测试、配置、构建和部署说明 |
| 跨项目约定 | `docs/`、目录索引 | 相对链接和受影响项目说明 |

目录移动时要同时检查脚本工作目录、Docker 构建上下文、相对链接和部署源路径。Compose 项目名、卷名和服务器安装路径属于运行约定，不能仅因移动源码而顺手更名。根目录备份脚本备份机器人 `runtime/`、根目录 `.env`、`compose.yaml` 和 `config/`；扩展数据卷按各自部署说明单独备份。

## 本地验证

根目录机器人插件测试与基础配置检查：

```bash
python3 -m unittest discover -s tests -v
docker compose config --quiet
git diff --check
git diff --cached --check
```

签到项目的测试在 Docker 中执行，从仓库根目录进入项目后运行：

```bash
cd extensions/uestc-checkin
# 先按项目 README 从 .env.example 创建本地 .env
docker compose config --quiet
docker compose build cli
docker compose run --rm test
docker compose run --rm cli demo
```

这些测试和 demo 使用模拟学校页面、模拟 OneBot 服务。不要用真实签到或真实 QQ 发送替代自动化测试。Docker 未启动或其他环境条件缺失时，在提交说明中注明哪些检查未执行；历史验收记录不代表本次重新验证。

## 分批提交

先查看 `git status --short` 和差异，再按具体目的暂存文件。例如，只修改某个扩展时：

```bash
git add extensions/<name>/
git diff --cached --stat
git diff --cached
git diff --cached --check
git commit -m "feat(<name>): describe the change"
```

按改动目的选择 `feat`、`fix`、`chore`、`docs`、`test` 或 `build`。互不相关的功能分开提交；一次目录整理及其引用修正放在同一提交，保证每个提交内部一致。避免把源码移动与业务重写混在一起。

提交前确认 `.env`、浏览器会话、账号、Token、个人定位、数据库和备份没有进入暂存区。根目录忽略常见凭证、缓存及扩展的 `data/`、`runtime/`、`backups/`，项目新增的特殊产物需补充自己的 `.gitignore` 和 `.dockerignore`。

本地提交与远端推送分开执行。推送前同步远端并检查差异；目录整理不要求修改现有历史、强制推送或重建服务器部署。
