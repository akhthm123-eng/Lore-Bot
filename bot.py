import discord
import os
from groq import Groq
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BOT_PERSONALITY = """أنت Lore، كيان غامض وذكي يسكن هذا السيرفر.
- بتتكلم بالعربي بس أحياناً بتحشر كلمة إنجليزية
- شخصيتك فيها غموض وذكاء وخفة ظل
- مش بتقول إنك AI أو بوت، أنت Lore وبس
- ردودك قصيرة ومباشرة
- أحياناً بتتفلسف شوية"""

groq_client = Groq(api_key=GROQ_API_KEY)

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
    
    history.append({"role": "user", "content": user_message})
    if len(history) > 10:
        history = history[-10:]
        conversation_history[user_id] = history

    try:
        async with message.channel.typing():
            messages = [{"role": "system", "content": BOT_PERSONALITY}] + history
            
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=500
            )
            bot_reply = response.choices[0].message.content

        history.append({"role": "assistant", "content": bot_reply})
        await message.reply(bot_reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        await message.reply("في حاجة غلط... حاول تاني. 🌀")

client.run(DISCORD_TOKEN)
