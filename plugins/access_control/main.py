import hashlib
import html

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import At, Plain
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star


class AccessControl(Star):
    """Apply the local QQ bot's conversation and command access policy."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1000)
    async def enforce(self, event: AstrMessageEvent):
        """Observe normal group chat while reserving commands for the owner."""
        if event.get_platform_name() != "aiocqhttp":
            return

        if event.is_admin():
            return

        messages = event.get_messages()
        first_component = next(
            (
                component
                for component in messages
                if not (isinstance(component, Plain) and not component.text.strip())
            ),
            None,
        )
        if (
            not event.is_private_chat()
            and isinstance(first_component, At)
            and str(first_component.qq) not in {str(event.get_self_id()), "all"}
        ):
            # The plain-text projection drops At components. Without this
            # guard, "@another-bot /command" looks like "/command" and this
            # bot incorrectly rejects a command that was not addressed to it.
            return

        original_text = "".join(
            component.text
            for component in messages
            if isinstance(component, Plain)
        ).strip()
        if original_text.startswith("/"):
            yield event.plain_result(self.config["command_denied_message"])
            event.stop_event()

    @filter.on_llm_request()
    async def inject_relationship(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """Inject the configured relationship for the current QQ user."""
        if event.get_platform_name() != "aiocqhttp":
            return

        if not self.config["is_relationship"]:
            return

        if req.system_prompt is None:
            req.system_prompt = ""

        sender_id = event.get_sender_id()
        is_relationship = event.is_admin()

        if is_relationship:
            relationship = self.config["relationship_prompt"]
        else:
            relationship = self.config["non_relationship_prompt"]

        req.system_prompt += f"\n# Current Relationship\n\n{relationship}\n"

        if not event.is_private_chat():
            # Group conversations share one history. Prefix the prompt so the
            # speaker identity is persisted with the user turn in that history.
            speaker_key = hashlib.sha256(
                f"qq-bot-speaker:{sender_id}".encode("utf-8")
            ).hexdigest()[:10]
            nickname = html.escape(event.get_sender_name()[:64], quote=True)
            role = "relationship" if is_relationship else "group_member"
            req.prompt = (
                "<qq_speaker>\n"
                f"stable_id: member-{speaker_key}\n"
                f"nickname: {nickname or '未设置昵称'}\n"
                f"relationship: {role}\n"
                "</qq_speaker>\n"
                "下面是这位发言者当前发送的内容。回复时只把它归属于上述发言者；"
                "不要把群聊历史中其他人的身份、称呼或经历转移给此人。\n\n"
                f"{req.prompt}"
            )
