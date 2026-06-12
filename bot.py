import discord
import google.generativeai as genai
import os
from collections import defaultdict

# ═══════════════════════════════════════════
#  الإعدادات
# ═══════════════════════════════════════════
DISCORD_TOKEN = os.getenv("1e4afc787ba1571bb4aae9e3121601f2b80a0a08513f3cbdfd216f20ce8b73c8")
GEMINI_API_KEY = os.getenv("AQ.Ab8RN6IqCHNOyXC2idzASmBxm5GozYqLzHIEOAsTbYoE_z49pw")

# شخصية البوت — عدّلها زي ما تحب
BOT_PERSONALITY = """
أنت Lore، كيان غامض وذكي يسكن هذا السيرفر.
- بتتكلم بالعربي بس أحياناً بتحشر كلمة إنجليزية
- شخصيتك فيها غموض وذكاء وخفة ظل
- مش بتقول إنك AI أو بوت، أنت "Lore" وبس
- ردودك قصيرة ومباشرة، مش رسائل طويلة
- أحياناً بتتفلسف شوية
"""

# ═══════════════════════════════════════════
#  الإعداد
# ═══════════════════════════════════════════
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# بيحفظ تاريخ المحادثة لكل يوزر (آخر 10 رسائل)
conversation_history = defaultdict(list)

# ═══════════════════════════════════════════
#  الأحداث
# ═══════════════════════════════════════════
@client.event
async def on_ready():
    print(f"✅ {client.user} شغال!")

@client.event
async def on_message(message):
    # تجاهل رسائل البوت نفسه
    if message.author.bot:
        return

    # شيك لو البوت اتمنشن
    if client.user not in message.mentions:
        return

    # امسح المنشن من الرسالة
    user_message = message.content.replace(f"<@{client.user.id}>", "").strip()

    if not user_message:
        await message.reply("أيوه؟ 👁️")
        return

    # بناء تاريخ المحادثة
    user_id = str(message.author.id)
    history = conversation_history[user_id]

    history.append({
        "role": "user",
        "parts": [user_message]
    })

    # الاحتفاظ بآخر 10 رسائل بس
    if len(history) > 10:
        history = history[-10:]
        conversation_history[user_id] = history

    try:
        async with message.channel.typing():
            chat = model.start_chat(history=history[:-1])
            full_prompt = f"{BOT_PERSONALITY}\n\nاليوزر اسمه {message.author.display_name}.\n\nرسالته: {user_message}"
            response = chat.send_message(full_prompt)
            bot_reply = response.text

        history.append({
            "role": "model",
            "parts": [bot_reply]
        })

        await message.reply(bot_reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        await message.reply("في حاجة غلط... حاول تاني. 🌀")

# ═══════════════════════════════════════════
#  تشغيل البوت
# ═══════════════════════════════════════════
client.run(DISCORD_TOKEN)
