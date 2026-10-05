import asyncio
import importlib.util
import inspect
import json
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
        def decorate(function):
            function.event_priority = _kwargs.get("priority", 0)
            return function

        return decorate

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
        sender_id: str | int = "sender",
        platform: str = "aiocqhttp",
    ):
        self.messages = messages
        self.private = private
        self.self_id = self_id
        self.admin = admin
        self.sender_id = sender_id
        self.platform = platform
        self.stopped = False

    def get_platform_name(self):
        return self.platform

    def is_admin(self):
        return self.admin

    def is_private_chat(self):
        return self.private

    def get_messages(self):
        return self.messages

    def get_self_id(self):
        return self.self_id

    def get_sender_id(self):
        return self.sender_id

    def get_sender_name(self):
        return "Sender"

    def plain_result(self, text):
        return text

    def stop_event(self):
        self.stopped = True


def enforce(event, message="当前账号仅支持聊天，不能使用机器人指令。", **overrides):
    plugin = ACCESS_CONTROL.AccessControl(
        None,
        {"command_denied_message": message, **overrides},
    )

    async def collect():
        await plugin.ignore_sender(event)
        if event.stopped:
            return []
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
    def test_ignored_group_sender_is_silently_stopped(self):
        event = FakeEvent([At("bot"), Plain("hello")], sender_id="3889001741")

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertTrue(event.stopped)

    def test_ignored_background_group_message_is_stopped(self):
        event = FakeEvent([Plain("自动通知")], sender_id="3889001741")

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertTrue(event.stopped)

    def test_ignored_command_does_not_send_denial_reply(self):
        event = FakeEvent([At("bot"), Plain(" //reset")], sender_id="3889001741")

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertTrue(event.stopped)

    def test_ignored_admin_does_not_bypass_filter(self):
        event = FakeEvent([Plain("hello")], sender_id="3153577174", admin=True)

        self.assertEqual(enforce(event, ignored_qq_ids=["3153577174"]), [])
        self.assertTrue(event.stopped)

    def test_ignored_private_sender_is_stopped(self):
        event = FakeEvent([Plain("hello")], sender_id="3889001741", private=True)

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertTrue(event.stopped)

    def test_ignore_list_accepts_numeric_ids_and_surrounding_whitespace(self):
        for sender_id, ignored_qq_ids in [
            (3889001741, [" 3889001741 "]),
            ("3889001741", [3889001741]),
        ]:
            with self.subTest(sender_id=sender_id):
                event = FakeEvent([Plain("hello")], sender_id=sender_id)
                self.assertEqual(enforce(event, ignored_qq_ids=ignored_qq_ids), [])
                self.assertTrue(event.stopped)

    def test_ignore_list_uses_exact_account_matches(self):
        event = FakeEvent([Plain("hello")], sender_id="38890017410")

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertFalse(event.stopped)

    def test_ignore_list_does_not_affect_other_platforms(self):
        event = FakeEvent(
            [Plain("hello")], sender_id="3889001741", platform="other-platform"
        )

        self.assertEqual(enforce(event, ignored_qq_ids=["3889001741"]), [])
        self.assertFalse(event.stopped)

    def test_webui_list_can_add_and_remove_senders(self):
        schema_path = (
            Path(__file__).resolve().parents[1]
            / "plugins" / "access_control" / "_conf_schema.json"
        )
        schema = json.loads(schema_path.read_text())
        self.assertEqual(schema["ignored_qq_ids"]["type"], "list")
        self.assertEqual(schema["ignored_qq_ids"]["default"], [])
        config = {key: item["default"] for key, item in schema.items()}

        async def check_saved_config():
            for ignored_qq_ids, should_stop in [
                ([], False), (["3889001741"], True), ([], False)
            ]:
                # WebUI persists JSON and reloads the plugin with that config.
                config["ignored_qq_ids"] = ignored_qq_ids
                plugin = ACCESS_CONTROL.AccessControl(
                    None, json.loads(json.dumps(config))
                )
                event = FakeEvent([Plain("hello")], sender_id="3889001741")
                await plugin.ignore_sender(event)
                self.assertEqual(event.stopped, should_stop)

        asyncio.run(check_saved_config())

    def test_filter_precedes_builtin_session_and_history_handlers(self):
        calls = []
        plugin = ACCESS_CONTROL.AccessControl(None, {"ignored_qq_ids": ["3889001741"]})

        async def session_control(event):
            calls.append("session_control")

        async def empty_mention(event):
            calls.append("empty_mention")

        async def persist_history(event):
            calls.append("history")

        async def group_context(event):
            calls.append("group_context")

        # Match AstrBot's descending priority order and stop propagation. The
        # built-in handlers use maxsize through maxsize - 2 and zero for ICL.
        handlers = [
            (0, group_context),
            (sys.maxsize - 2, persist_history),
            (sys.maxsize - 1, empty_mention),
            (sys.maxsize, session_control),
            (plugin.ignore_sender.event_priority, plugin.ignore_sender),
            (plugin.enforce.event_priority, plugin.enforce),
        ]

        async def dispatch(event):
            for _, handler in sorted(handlers, key=lambda item: -item[0]):
                if event.stopped:
                    break
                result = handler(event)
                if inspect.isasyncgen(result):
                    async for _ in result:
                        pass
                else:
                    await result

        for messages in [[At("bot")], [Plain("notice")]]:
            event = FakeEvent(messages, sender_id="3889001741")
            asyncio.run(dispatch(event))
            self.assertTrue(event.stopped)
            self.assertEqual(calls, [])

        event = FakeEvent([Plain("hello")], sender_id="3153577174")
        asyncio.run(dispatch(event))
        self.assertFalse(event.stopped)
        self.assertEqual(
            calls, ["session_control", "empty_mention", "history", "group_context"]
        )

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
