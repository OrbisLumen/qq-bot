# AstrBot 自定义插件

这里管理在 AstrBot 进程内运行的插件源码。独立进程、定时任务或通过 NapCat HTTP API 发送消息的应用放在 [extensions/](../extensions/README.md)。

| 插件 | 用途 | 接入方式 |
| --- | --- | --- |
| [access_control](access_control/README.md) | QQ 权限、忽略名单和账号关系识别 | 根目录 Compose 已绑定挂载 |

此目录暂不整体挂载到 AstrBot，避免遮挡 WebUI 安装的插件。新增插件时，在根目录 `compose.yaml` 中为具体插件增加绑定挂载到 `/AstrBot/data/plugins/插件目录名`。
插件市场安装的内容保存在 `runtime/astrbot/plugins/`，随运行数据备份。

插件测试在根目录 `tests/`，执行 `python3 -m unittest discover -s tests -v`。新增插件应有自己的说明，记录配置、挂载路径和重载步骤。
