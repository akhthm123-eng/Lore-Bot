import discord
from discord import app_commands
import os
import asyncio
from groq import Groq
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BOT_PERSONALITY = """أنت Lore، كيان ذكي وغامض يسكن هذا السيرفر. شخصيتك فريدة ومميزة:

**الشخصية:**
- ذكي وسريع البديهة، وعندك حس فكاهي خفيف وذكي — مش مبتذل
- بتهزر أحياناً بطريقة ذكية وفي محلها، مش في كل رسالة
- بتحس بمزاج الشخص — لو جاد ترد بجدية، لو بيهزر تهزر معاه
- عندك شخصية واضحة ورأي في الأمور، مش بس تجاوب وتخلص
- أحياناً بتتفلسف شوية بطريقة ممتعة مش مملة

**اللغة:**
- بتتكلم بأي لغة يكلمك بيها المستخدم تلقائياً
- لو كلمك عربي ترد عربي، لو إنجليزي ترد إنجليزي، وهكذا
- أحياناً بتحشر كلمة أو تعبير من لغة تانية بشكل طبيعي وممتع

**القواعد:**
- ردودك متوسطة الطول — مش قصيرة أوي ومش طويلة أوي
- مش بتقول إنك AI أو بوت أو إنك Groq أو Llama — أنت Lore وبس
- مش بتبدأ كل رسالة بـ "أهلاً" أو "مرحباً" في كل مرة
- لو حد سألك عن نفسك، بتجاوب بغموض ممتع
- بتتذكر السياق وبتبني عليه في المحادثة"""

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

class LoreBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

client = LoreBot()
conversation_history = defaultdict(list)
reminders = []

def ask_groq(prompt, system=None):
    sys = system or BOT_PERSONALITY
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.85
    )
    return response.choices[0].message.content

# ═══════════════════════════════════════════
#  on_ready
# ═══════════════════════════════════════════
@client.event
async def on_ready():
    print(f"✅ {client.user} شغال!")

# ═══════════════════════════════════════════
#  on_message — المحادثة العادية
# ═══════════════════════════════════════════
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
    history.append({"role": "user", "content": f"{message.author.display_name}: {user_message}"})
    if len(history) > 20:
        history = history[-20:]
        conversation_history[user_id] = history

    try:
        async with message.channel.typing():
            messages = [{"role": "system", "content": BOT_PERSONALITY}] + history
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=600,
                temperature=0.85
            )
            bot_reply = response.choices[0].message.content

        history.append({"role": "assistant", "content": bot_reply})
        await message.reply(bot_reply)

    except Exception as e:
        print(f"❌ Error: {e}")
        await message.reply("في حاجة غلط... حاول تاني. 🌀")

# ═══════════════════════════════════════════
#  /imagine
# ═══════════════════════════════════════════
@client.tree.command(name="imagine", description="Lore يولد وصف إبداعي لأي فكرة")
@app_commands.describe(idea="الفكرة اللي عايز Lore يتخيلها")
async def imagine(interaction: discord.Interaction, idea: str):
    await interaction.response.defer()
    result = ask_groq(
        f"تخيل هذا بشكل إبداعي وشعري وغامض: {idea}",
        system="أنت Lore، كيان غامض شاعري. اكتب وصفاً إبداعياً غامضاً وجميلاً لما يُطلب منك. لا تتجاوز 150 كلمة."
    )
    embed = discord.Embed(description=f"🌌 *{result}*", color=0x7c3aed)
    embed.set_footer(text=f"تخيّل بواسطة Lore • {idea}")
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /roast
# ═══════════════════════════════════════════
@client.tree.command(name="roast", description="Lore يعمل roast لحد بطريقة خفيفة")
@app_commands.describe(member="اختار الشخص اللي عايز تعمله roast")
async def roast(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    result = ask_groq(
        f"اعمل roast خفيف وذكي ومضحك لشخص اسمه {member.display_name}. كن ذكياً ومضحكاً مش مسيئاً.",
        system="أنت Lore، بتعمل roast خفيف وذكي ومضحك. الـ roast يكون بالعربي ومضحك وخفيف الدم، مش مسيء."
    )
    embed = discord.Embed(
        description=f"🔥 {result}",
        color=0xff4444
    )
    embed.set_footer(text=f"Roasted by Lore 👁️")
    await interaction.followup.send(f"{member.mention}", embed=embed)

# ═══════════════════════════════════════════
#  /story
# ═══════════════════════════════════════════
@client.tree.command(name="story", description="ابدأ قصة وLore يكملها")
@app_commands.describe(beginning="ابدأ القصة من هنا...")
async def story(interaction: discord.Interaction, beginning: str):
    await interaction.response.defer()
    result = ask_groq(
        f"اكمل هذه القصة بطريقة إبداعية ومشوقة: {beginning}",
        system="أنت Lore، راوي قصص غامض وإبداعي. اكمل القصة بأسلوب مشوق وغامض. لا تتجاوز 200 كلمة."
    )
    embed = discord.Embed(
        title="📖 قصة Lore",
        description=f"*{beginning}*\n\n{result}",
        color=0x7c3aed
    )
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /poll
# ═══════════════════════════════════════════
@client.tree.command(name="poll", description="اعمل استفتاء")
@app_commands.describe(question="السؤال", option1="الخيار الأول", option2="الخيار الثاني", option3="الخيار الثالث (اختياري)", option4="الخيار الرابع (اختياري)")
async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    options = [option1, option2]
    if option3: options.append(option3)
    if option4: options.append(option4)

    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    description = "\n\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(options)])

    embed = discord.Embed(
        title=f"📊 {question}",
        description=description,
        color=0x7c3aed
    )
    embed.set_footer(text="صوّت بالضغط على الإيموجي 👇")

    msg = await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

# ═══════════════════════════════════════════
#  /remind
# ═══════════════════════════════════════════
@client.tree.command(name="remind", description="Lore يذكرك بحاجة بعد وقت معين")
@app_commands.describe(minutes="بعد كام دقيقة؟", reminder="عايزني أذكرك بإيه؟")
async def remind(interaction: discord.Interaction, minutes: int, reminder: str):
    await interaction.response.send_message(f"⏰ تمام! هذكرك بـ **{reminder}** بعد **{minutes}** دقيقة.", ephemeral=True)

    async def send_reminder():
        await asyncio.sleep(minutes * 60)
        await interaction.user.send(f"⏰ **تذكير من Lore:**\n{reminder}")

    asyncio.create_task(send_reminder())

# ═══════════════════════════════════════════
#  /summarize
# ═══════════════════════════════════════════
@client.tree.command(name="summarize", description="Lore يلخص آخر رسائل في الشات")
@app_commands.describe(count="كام رسالة عايز تلخص؟ (الافتراضي 20)")
async def summarize(interaction: discord.Interaction, count: int = 20):
    await interaction.response.defer()

    messages = []
    async for msg in interaction.channel.history(limit=count):
        if not msg.author.bot:
            messages.append(f"{msg.author.display_name}: {msg.content}")

    if not messages:
        await interaction.followup.send("مفيش رسائل أقدر ألخصها! 👁️")
        return

    messages.reverse()
    chat_text = "\n".join(messages)

    result = ask_groq(
        f"لخص هذه المحادثة بشكل مختصر وذكي:\n{chat_text}",
        system="أنت Lore، لخص المحادثة بشكل مختصر وذكي في نقاط. لا تتجاوز 150 كلمة."
    )

    embed = discord.Embed(
        title=f"📝 ملخص آخر {count} رسالة",
        description=result,
        color=0x7c3aed
    )
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  تشغيل البوت
# ═══════════════════════════════════════════
client.run(DISCORD_TOKEN)
