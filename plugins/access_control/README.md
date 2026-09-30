# Access Control

`access_control` 是当前 QQ Bot 部署使用的本地 AstrBot 插件，用于限制机器人指令权限，并为模型补充当前 QQ 发言者的身份关系。

## 功能

- 仅处理 `aiocqhttp` 平台事件，其他平台不受影响。
- AstrBot 管理员可以正常使用 `/` 指令。
- 非管理员发送 `/` 指令时，插件终止该事件并返回可配置的提示语。
- 群聊消息以 `@其他账号` 开头时，不会被误判为发给当前机器人的指令。
- 可通过 WebUI 开启或关闭关系身份注入。
- 请求大模型前，根据 AstrBot 管理员身份注入可配置的特殊关系或普通成员关系说明。
- 群聊请求会附带经过哈希处理的稳定发言者标识，降低共享会话中身份串线的概率。

管理员身份来自 AstrBot WebUI 中配置的管理员账号，插件不硬编码 QQ 号。

## 指令拦截规则

| 场景 | 非管理员的处理结果 |
| --- | --- |
| 私聊发送 `/help` | 拦截并回复提示语 |
| 群聊发送 `/help` | 拦截并回复提示语 |
| 群聊发送 `@当前机器人 /help` | 拦截并回复提示语 |
| 群聊发送 `@其他机器人 /help` | 忽略，不回复也不终止事件 |
| 普通聊天 | 不拦截 |

## WebUI 配置

插件目录中的 `_conf_schema.json` 会被 AstrBot 自动识别，并在 WebUI 的插件配置页面生成表单。

1. 打开 AstrBot WebUI。
2. 进入插件管理，找到 `access_control`。
3. 打开插件配置。
4. 修改指令拦截回复、关系身份开关或关系提示词。
5. 保存配置。AstrBot 会自动热重载插件，新配置随后生效。

| 配置字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `command_denied_message` | `text` | `当前账号仅支持聊天，不能使用机器人指令。` | 非管理员触发 `/` 指令拦截时发送的回复 |
| `is_relationship` | `bool` | `true` | 是否启用关系提示词及群聊发言者标签注入 |
| `relationship_prompt` | `text` | 内置“哥哥”关系提示词 | 当前发言者是 AstrBot 管理员时注入的系统提示词 |
| `non_relationship_prompt` | `text` | 内置普通成员关系提示词 | 当前发言者不是 AstrBot 管理员时注入的系统提示词 |

`is_relationship` 只负责开启或关闭关系注入。特殊关系的成员范围仍由 AstrBot 管理员列表决定；修改管理员列表不需要改插件配置。

启用关系注入时，群聊请求中的特殊关系角色统一标记为 `relationship`，不再在内部协议中写死为 `brother`。具体称呼和关系由 `relationship_prompt` 决定。

AstrBot 会将配置持久化到数据目录下的 `config/access_control_config.json`。该运行时文件由 WebUI 管理，不需要手动修改。

## 部署

本项目通过 `compose.yaml` 将插件目录只读挂载到 AstrBot 容器：

```text
./plugins/access_control:/AstrBot/data/plugins/access_control:ro
```

插件配置保存在单独的 AstrBot 数据卷中，因此插件源码保持只读不会影响 WebUI 保存配置。

修改插件源码或 `_conf_schema.json` 后，需要重载插件或重启 AstrBot，AstrBot 才会重新载入代码和配置 Schema。

## 本地测试

在项目根目录运行：

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖向其他机器人发指令、向当前机器人发指令、无 `@` 群聊指令、私聊指令、自定义回复文案以及关系注入配置。
