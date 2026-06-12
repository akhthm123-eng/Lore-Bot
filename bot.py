import discord
import os
import google.generativeai as genai
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BOT_PERSONALITY = """أنت Lore، كيان غامض وذكي يسكن هذا السيرفر.
- بتتكلم بالعربي بس أحياناً بتحشر كلمة إنجليزية
- شخصيتك فيها غموض وذكاء وخفة ظل
- مش بتقول إنك AI أو بوت، أنت Lore وبس
- ردودك قصيرة ومباشرة
- أحياناً بتتفلسف شوية"""

genai.configure(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

conversation_history = defaultdict(list)

@client.event
async def on_ready():
    print(f"✅ {client.user} شغال!")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if client.user not in message.mentions:
        return

    user_message = message.content.replace(f"<@{client.user.id}>", "").strip()

    if not user_message:
        await message.reply("أيوه؟ 👁️")
        return

    user_id = str(message.author.id)
    history = conversation_history[user_id]
    history.append(f"المستخدم: {user_message}")
    if len(history) > 10:
        history = history[-10:]
        conversation_history[user_id] = history

    try:
        async with message.channel.typing():
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            full_prompt = f"""{BOT_PERSONALITY}

تاريخ المحادثة:
{chr(10).join(history[:-1])}

المستخدم اسمه {message.author.display_name} وقالك: {user_message}

ردك:"""
            
            response = model.generate_content(full_prompt)
            bot_reply = response.text

        history.append(f"Lore: {bot_reply}")
        await message.reply(bot_reply)

    except Exception as e:
        print(f"❌ Gemini Error: {e}")
        await message.reply("في حاجة غلط... حاول تاني. 🌀")

client.run(DISCORD_TOKEN)
