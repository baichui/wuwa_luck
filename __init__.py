# -*- coding: utf-8 -*-
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.plugin import PluginMetadata

from .config import character_weights, load_config
from .image import get_image
from .updater import update_plugin

__plugin_meta__ = PluginMetadata(
    name="WuWaLuck|今日运势",
    description="鸣潮主题白底今日运势图；config.json 可配权重；/更新luck 自更新",
    usage="/luck /今日运势 /更新luck",
    type="application",
    homepage="https://github.com/baichui/wuwa_luck",
    supported_adapters={"~onebot.v11"},
)

wuwa_luck = on_command(
    "luck",
    aliases={"今日运势"},
    priority=5,
    block=True,
)

update_luck = on_command(
    "更新luck",
    aliases={"更新运势", "luck更新"},
    priority=5,
    block=True,
)


@update_luck.handle()
async def _(event: MessageEvent):
    try:
        msg = await update_plugin("nonebot")
    except Exception as e:  # noqa: BLE001
        logger.exception("wuwa_luck: update failed")
        await update_luck.finish(f"更新失败：{e}")
        return
    await update_luck.finish(msg)


@wuwa_luck.handle()
async def _(event: MessageEvent, bot: Bot):
    user_id = event.user_id
    nickname = ""

    if isinstance(event, PrivateMessageEvent):
        nickname = event.sender.nickname or str(user_id)
    elif isinstance(event, GroupMessageEvent):
        try:
            info = await bot.get_group_member_info(group_id=event.group_id, user_id=user_id)
            nickname = info.get("card") or info.get("nickname") or str(user_id)
        except Exception as e:  # noqa: BLE001
            logger.warning(f"wuwa_luck: get group member info failed: {e}")
            nickname = event.sender.nickname or str(user_id)
    else:
        nickname = str(user_id)

    try:
        cfg = load_config()
        image = get_image(
            nickname=nickname,
            uid=user_id,
            character_weights=character_weights(cfg) or None,
            wuwa_deed_chance=float(cfg.get("wuwa_deed_chance", 0.3)),
            metric_labels=cfg.get("metric_labels") or None,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("wuwa_luck: render failed")
        await wuwa_luck.finish(f"运势图生成失败：{e}")

    if isinstance(event, PrivateMessageEvent):
        await wuwa_luck.send(MessageSegment.image(image))
    else:
        await wuwa_luck.send(MessageSegment.at(user_id) + MessageSegment.image(image))
