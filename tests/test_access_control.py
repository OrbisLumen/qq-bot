import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path


class Plain:
    def __init__(self, text: str) -> None:
        self.text = text


class At:
    def __init__(self, qq: str) -> None:
        self.qq = qq


class _Filter:
    class EventMessageType:
        ALL = object()

    @staticmethod
    def event_message_type(*_args, **_kwargs):
        return lambda function: function

    @staticmethod
    def on_llm_request(*_args, **_kwargs):
        return lambda function: function


class _Star:
    def __init__(self, context) -> None:
        self.context = context


def _load_plugin():
    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    api.AstrBotConfig = dict
    event = types.ModuleType("astrbot.api.event")
    event.AstrMessageEvent = object
    event.filter = _Filter
    components = types.ModuleType("astrbot.api.message_components")
    components.At = At
    components.Plain = Plain
    provider = types.ModuleType("astrbot.api.provider")
    provider.ProviderRequest = object
    star = types.ModuleType("astrbot.api.star")
    star.Context = object
    star.Star = _Star

    modules = {
        "astrbot": astrbot,
        "astrbot.api": api,
        "astrbot.api.event": event,
        "astrbot.api.message_components": components,
        "astrbot.api.provider": provider,
        "astrbot.api.star": star,
    }
    sys.modules.update(modules)

    plugin_path = (
        Path(__file__).resolve().parents[1] / "plugins" / "access_control" / "main.py"
    )
    spec = importlib.util.spec_from_file_location("access_control_main", plugin_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ACCESS_CONTROL = _load_plugin()


class FakeEvent:
    def __init__(
        self,
        messages,
        *,
        private: bool = False,
        self_id: str = "bot",
        admin: bool = False,
    ):
        self.messages = messages
        self.private = private
        self.self_id = self_id
        self.admin = admin
        self.stopped = False

    def get_platform_name(self):
        return "aiocqhttp"

    def is_admin(self):
        return self.admin

    def is_private_chat(self):
        return self.private

    def get_messages(self):
        return self.messages

    def get_self_id(self):
        return self.self_id

    def get_sender_id(self):
        return "sender"

    def get_sender_name(self):
        return "Sender"

    def plain_result(self, text):
        return text

    def stop_event(self):
        self.stopped = True


def enforce(event, message="当前账号仅支持聊天，不能使用机器人指令。"):
    plugin = ACCESS_CONTROL.AccessControl(
        None,
        {"command_denied_message": message},
    )

    async def collect():
        return [result async for result in plugin.enforce(event)]

    return asyncio.run(collect())


def inject_relationship(event, **overrides):
    config = {
        "is_relationship": True,
        "relationship_prompt": "special relationship",
        "non_relationship_prompt": "ordinary relationship",
    }
    config.update(overrides)
    plugin = ACCESS_CONTROL.AccessControl(None, config)
    request = types.SimpleNamespace(system_prompt="base", prompt="hello")
    asyncio.run(plugin.inject_relationship(event, request))
    return request


class AccessControlTests(unittest.TestCase):
    def test_group_command_addressed_to_another_bot_is_ignored(self):
        event = FakeEvent([At("other-bot"), Plain(" /help")])

        self.assertEqual(enforce(event), [])
        self.assertFalse(event.stopped)

    def test_whitespace_before_other_bot_mention_is_ignored(self):
        event = FakeEvent([Plain(" "), At("other-bot"), Plain(" /help")])

        self.assertEqual(enforce(event), [])
        self.assertFalse(event.stopped)

    def test_group_command_addressed_to_this_bot_is_rejected(self):
        event = FakeEvent([At("bot"), Plain(" /help")])

        self.assertEqual(
            enforce(event),
            ["当前账号仅支持聊天，不能使用机器人指令。"],
        )
        self.assertTrue(event.stopped)

    def test_unmentioned_group_command_is_rejected(self):
        event = FakeEvent([Plain("/help")])

        self.assertEqual(
            enforce(event),
            ["当前账号仅支持聊天，不能使用机器人指令。"],
        )
        self.assertTrue(event.stopped)

    def test_private_command_keeps_existing_behavior(self):
        event = FakeEvent([At("other-bot"), Plain(" /help")], private=True)

        self.assertEqual(
            enforce(event),
            ["当前账号仅支持聊天，不能使用机器人指令。"],
        )
        self.assertTrue(event.stopped)

    def test_command_denied_message_uses_plugin_config(self):
        event = FakeEvent([Plain("/help")])

        self.assertEqual(enforce(event, "这里不能使用指令。"), ["这里不能使用指令。"])
        self.assertTrue(event.stopped)

    def test_relationship_injection_can_be_disabled(self):
        event = FakeEvent([Plain("hello")], admin=True)

        request = inject_relationship(event, is_relationship=False)

        self.assertEqual(request.system_prompt, "base")
        self.assertEqual(request.prompt, "hello")

    def test_admin_uses_configured_relationship_prompt(self):
        event = FakeEvent([Plain("hello")], admin=True)

        request = inject_relationship(event)

        self.assertIn("special relationship", request.system_prompt)
        self.assertIn("relationship: relationship", request.prompt)

    def test_non_admin_uses_configured_non_relationship_prompt(self):
        event = FakeEvent([Plain("hello")])

        request = inject_relationship(event)

        self.assertIn("ordinary relationship", request.system_prompt)
        self.assertIn("relationship: group_member", request.prompt)


if __name__ == "__main__":
    unittest.main()
