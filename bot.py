# app.py
# Don't Remove Credit @teacher_slex
# Subscribe YouTube ƈɦǟռռɛʟ For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import asyncio
import logging

from aiohttp import web
from pyrogram import Client, filters, idle, errors
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors.exceptions.flood_420 import FloodWait

from database import add_user, add_group, all_users, all_groups, users
from configs import cfg

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- Telegram client ----------
tg = Client(
    "approver",
    api_id=cfg.API_ID,
    api_hash=cfg.API_HASH,
    bot_token=cfg.BOT_TOKEN
)

#━━━━━━━━━━━━━━━━━━━━ HELPER ━━━━━━━━━━━━━━━━━━━━
def parse_post_link(link: str):
    parts = link.rstrip("/").split("/")
    chat = parts[-2]
    msg_id = int(parts[-1])
    return chat, msg_id

#━━━━━━━━━━━━━━━━━━━━ JOIN REQUEST (AUTO APPROVE + OLD DM) ━━━━━━━━━━━━━━━━━━━━
@tg.on_chat_join_request(filters.group | filters.channel)
async def approve(_, m):
    op = m.chat
    user = m.from_user

    try:
        add_group(op.id)
        add_user(user.id)

        # ✅ JOIN REQUEST ACCEPT
        await tg.approve_chat_join_request(op.id, user.id)

        # ✅ SAME OLD DM MESSAGE
        try:
            await tg.send_message(
                user.id,
                f"👋 Hello • {user.first_name}\n\n"
                "🥀 Aapka join request approve ho gaya hai.\n"
                "⚡️ Important info niche aa gayi hai 👇"
            )
        except Exception:
            # user might have privacy settings; ignore
            pass

        # ✅ PROMO / POSTS SEND (if cfg.POSTS present)
        for link in getattr(cfg, "POSTS", []) or []:
            try:
                chat_id, msg_id = parse_post_link(link)
                await tg.copy_message(
                    chat_id=user.id,
                    from_chat_id=chat_id,
                    message_id=msg_id
                )
                await asyncio.sleep(1)
            except Exception:
                pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
    except errors.PeerIdInvalid:
        pass
    except Exception:
        log.exception("Error in approve handler")

#━━━━━━━━━━━━━━━━━━━━ START COMMAND ━━━━━━━━━━━━━━━━━━━━
@tg.on_message(filters.private & filters.command("start"))
async def start(_, m: Message):
    add_user(m.from_user.id)

    if m.from_user.id not in cfg.SUDO:
        await m.reply_text(
            "𝐁𝐇𝐀𝐈 𝐇𝐀𝐂𝐊 𝐒𝐄 𝐏𝐋𝐀𝐘 𝐊𝐑𝐎\n\n💸𝐏𝐑𝐎𝐅𝐈𝐓 𝐊𝐑𝐎🍻"
        )

        for link in getattr(cfg, "POSTS", []) or []:
            try:
                chat_id, msg_id = parse_post_link(link)
                await tg.copy_message(
                    chat_id=m.from_user.id,
                    from_chat_id=chat_id,
                    message_id=msg_id
                )
                await asyncio.sleep(1)
            except Exception:
                pass
        return

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🗯 ƈɦǟռռɛʟ", url="https://t.me/lnx_store"),
            InlineKeyboardButton("💬 Support", url="https://t.me/teacher_slex")
        ]]
    )

    await m.reply_photo(
        photo="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhsaR6kRdTPF2ZMEgmgSYjjXU6OcsJhkBe1EWtI1nfbOziINTYzxjlGCMSVh-KoH05Z8MpRWhVV9TIX_ykpjdeGqJ1atXy1TUqrVkohUxlykoZyl67EfMQppHoWYrdHmdi6FMcL9v-Vew2VtaWHWY_eGZt-GN057jLGvYj7UV49g0rXVxoDFXQAYxvaX1xP/s1280/75447.jpg",
        caption=(
            f"**🦊 Hello {m.from_user.mention}!**\n\n"
            "I'm an auto approve bot.\n"
            "I handle join requests & DM users.\n\n"
            "📢 Broadcast : /bcast\n"
            "📊 Users : /users\n\n"
            "__Powered By : @teacher_slex__"
        ),
        reply_markup=keyboard
    )

#━━━━━━━━━━━━━━━━━━━━ USERS COUNT ━━━━━━━━━━━━━━━━━━━━
@tg.on_message(filters.command("users") & filters.user(cfg.SUDO))
async def users_count(_, m: Message):
    u = all_users()
    g = all_groups()
    await m.reply_text(f"🙋 Users : `{u}`\n👥 Groups : `{g}`\n📊 Total : `{u+g}`")

#━━━━━━━━━━━━━━━━━━━━ BROADCAST ━━━━━━━━━━━━━━━━━━━━
@tg.on_message(filters.command("bcast") & filters.user(cfg.SUDO))
async def bcast(_, m: Message):
    if not m.reply_to_message:
        return await m.reply("Reply to a message to broadcast.")

    status = await m.reply("⚡ Broadcasting...")
    ok = fail = 0

    # iterate over users collection cursor
    for u in users.find():
        try:
            await m.reply_to_message.copy(u["user_id"])
            ok += 1
            # small delay to reduce flood risk
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            fail += 1

    await status.edit(f"✅ {ok} | ❌ {fail}")

# ---------- Simple aiohttp web server so Render sees an open port ----------
async def handle_index(request):
    return web.Response(text="🤖 Bot is alive and running!")

async def start_web_server(port: int):
    web_app = web.Application()
    web_app.router.add_get('/', handle_index)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    log.info(f"Web server started on port {port}")
    return runner  # so we can cleanup later

# ---------- Main: start bot + web in same event loop ----------
async def main():
    port = int(os.environ.get("PORT", "8080"))

    # start the web server
    web_runner = await start_web_server(port)

    # start the telegram bot (pyrogram) client
    await tg.start()
    print("🤖 Bot is Alive!")

    try:
        await idle()  # keeps the client running
    finally:
        await tg.stop()
        await web_runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
