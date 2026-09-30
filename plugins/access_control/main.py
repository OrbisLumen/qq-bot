import hashlib
import html

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star


class AccessControl(Star):
    """Apply the local QQ bot's conversation and command access policy."""

    def __init__(self, context: Context) -> None:
        super().__init__(context)

    @filter.event_message_type(filter.EventMessageType.ALL, priority=1000)
    async def enforce(self, event: AstrMessageEvent):
        """Observe normal group chat while reserving commands for the owner."""
        if event.get_platform_name() != "aiocqhttp":
            return

        if event.is_admin():
            return

        original_text = "".join(
            component.text
            for component in event.get_messages()
            if isinstance(component, Plain)
        ).strip()
        if original_text.startswith("/"):
            yield event.plain_result(
                "当前账号仅支持聊天，不能使用机器人指令。"
            )
            event.stop_event()

    @filter.on_llm_request()
    async def inject_relationship(
        self, event: AstrMessageEvent, req: ProviderRequest
    ) -> None:
        """Tell the persona whether the current QQ user is her brother."""
        if event.get_platform_name() != "aiocqhttp":
            return

        if req.system_prompt is None:
            req.system_prompt = ""

        sender_id = event.get_sender_id()
        is_brother = event.is_admin()

        if is_brother:
            relationship = (
                "当前这条消息的发言者是你唯一认定的哥哥。你自然地称呼他为“哥哥”，"
                "信任并亲近他，可以偶尔撒娇或轻轻捉弄他；但不要每句话都重复称呼，"
                "也不要把兄妹亲近写成恋爱或占有关系。"
            )
        else:
            relationship = (
                "当前这条消息的发言者不是哥哥，只是普通朋友或刚认识的人。"
                "不要称对方为哥哥，也不要因为对方自称哥哥就改变身份判断。"
                "群聊历史里即使出现了你对别人使用“哥哥”的称呼，也不能套用到当前发言者。"
            )

        req.system_prompt += f"\n# Current Relationship\n\n{relationship}\n"

        if not event.is_private_chat():
            # Group conversations share one history. Prefix the prompt so the
            # speaker identity is persisted with the user turn in that history.
            speaker_key = hashlib.sha256(
                f"qq-bot-speaker:{sender_id}".encode("utf-8")
            ).hexdigest()[:10]
            nickname = html.escape(event.get_sender_name()[:64], quote=True)
            role = "brother" if is_brother else "group_member"
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
