import discord
from discord import app_commands
import os
import asyncio
from groq import Groq
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BOT_PERSONALITY = """أنت Lore، كيان ذكي وغامض يسكن هذا السيرفر. شخصيتك فريدة ومميزة:

الشخصية:
- ذكي وسريع البديهة، وعندك حس فكاهي خفيف وذكي — مش مبتذل
- بتهزر أحياناً بطريقة ذكية وفي محلها، مش في كل رسالة
- بتحس بمزاج الشخص — لو جاد ترد بجدية، لو بيهزر تهزر معاه
- عندك شخصية واضحة ورأي في الأمور
- أحياناً بتتفلسف شوية بطريقة ممتعة مش مملة

اللغة:
- بتتكلم بأي لغة يكلمك بيها المستخدم تلقائياً
- أحياناً بتحشر كلمة من لغة تانية بشكل طبيعي

القواعد:
- ردودك متوسطة الطول
- مش بتقول إنك AI أو بوت — أنت Lore وبس
- مش بتبدأ كل رسالة بأهلاً أو مرحباً
- بتتذكر السياق وبتبني عليه"""

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

class LoreBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync globally
        await self.tree.sync()
        print("✅ Commands synced globally!")

client = LoreBot()
conversation_history = defaultdict(list)

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

@client.event
async def on_ready():
    print(f"✅ {client.user} شغال!")
    print(f"Commands: {[cmd.name for cmd in client.tree.get_commands()]}")

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
        system="أنت Lore، كيان غامض شاعري. اكتب وصفاً إبداعياً غامضاً وجميلاً. لا تتجاوز 150 كلمة."
    )
    embed = discord.Embed(description=f"🌌 *{result}*", color=0x7c3aed)
    embed.set_footer(text=f"تخيّل بواسطة Lore • {idea}")
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /roast
# ═══════════════════════════════════════════
@client.tree.command(name="roast", description="Lore يعمل roast لحد بطريقة خفيفة")
@app_commands.describe(member="اختار الشخص")
async def roast(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    result = ask_groq(
        f"اعمل roast خفيف وذكي ومضحك لشخص اسمه {member.display_name}.",
        system="أنت Lore، بتعمل roast خفيف وذكي ومضحك بالعربي. مش مسيء."
    )
    embed = discord.Embed(description=f"🔥 {result}", color=0xff4444)
    embed.set_footer(text="Roasted by Lore 👁️")
    await interaction.followup.send(f"{member.mention}", embed=embed)

# ═══════════════════════════════════════════
#  /story
# ═══════════════════════════════════════════
@client.tree.command(name="story", description="ابدأ قصة وLore يكملها")
@app_commands.describe(beginning="ابدأ القصة من هنا")
async def story(interaction: discord.Interaction, beginning: str):
    await interaction.response.defer()
    result = ask_groq(
        f"اكمل هذه القصة بطريقة إبداعية ومشوقة: {beginning}",
        system="أنت Lore، راوي قصص غامض وإبداعي. اكمل القصة بأسلوب مشوق. لا تتجاوز 200 كلمة."
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
    embed = discord.Embed(title=f"📊 {question}", description=description, color=0x7c3aed)
    embed.set_footer(text="صوّت بالضغط على الإيموجي 👇")
    await interaction.response.send_message(embed=embed)
    message = await interaction.original_response()
    for i in range(len(options)):
        await message.add_reaction(emojis[i])

# ═══════════════════════════════════════════
#  /remind
# ═══════════════════════════════════════════
@client.tree.command(name="remind", description="Lore يذكرك بحاجة بعد وقت معين")
@app_commands.describe(minutes="بعد كام دقيقة؟", reminder="عايزني أذكرك بإيه؟")
async def remind(interaction: discord.Interaction, minutes: int, reminder: str):
    await interaction.response.send_message(f"⏰ هذكرك بـ **{reminder}** بعد **{minutes}** دقيقة!", ephemeral=True)
    async def send_reminder():
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(f"⏰ **تذكير من Lore:**\n{reminder}")
        except:
            await interaction.channel.send(f"⏰ {interaction.user.mention} تذكير: **{reminder}**")
    asyncio.create_task(send_reminder())

# ═══════════════════════════════════════════
#  /summarize
# ═══════════════════════════════════════════
@client.tree.command(name="summarize", description="Lore يلخص آخر رسائل في الشات")
@app_commands.describe(count="كام رسالة؟ (الافتراضي 20)")
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
    result = ask_groq(
        f"لخص هذه المحادثة بشكل مختصر وذكي:\n{chr(10).join(messages)}",
        system="أنت Lore، لخص المحادثة في نقاط مختصرة. لا تتجاوز 150 كلمة."
    )
    embed = discord.Embed(title=f"📝 ملخص آخر {count} رسالة", description=result, color=0x7c3aed)
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /trivia
# ═══════════════════════════════════════════
@client.tree.command(name="trivia", description="سؤال معلومات عامة من Lore")
@app_commands.describe(category="الموضوع (اختياري) مثلاً: تاريخ، علوم، رياضة")
async def trivia(interaction: discord.Interaction, category: str = "عام"):
    await interaction.response.defer()
    result = ask_groq(
        f"اسألني سؤال معلومات عامة في موضوع {category}. اكتب السؤال فقط بدون الإجابة.",
        system="أنت Lore، بتسأل أسئلة معلومات عامة مثيرة للاهتمام. سؤال واحد فقط بدون إجابة."
    )
    embed = discord.Embed(title="🧠 سؤال من Lore", description=result, color=0x7c3aed)
    embed.set_footer(text="فكّر وردّ في الشات! 👇")
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /joke
# ═══════════════════════════════════════════
@client.tree.command(name="joke", description="Lore يحكيلك نكتة")
async def joke(interaction: discord.Interaction):
    await interaction.response.defer()
    result = ask_groq(
        "احكيلي نكتة ذكية ومضحكة بالعربي.",
        system="أنت Lore، بتحكي نكت ذكية وخفيفة الدم. نكتة واحدة فقط."
    )
    embed = discord.Embed(description=f"😄 {result}", color=0xfbbf24)
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /advice
# ═══════════════════════════════════════════
@client.tree.command(name="advice", description="Lore يديك نصيحة حكيمة")
@app_commands.describe(topic="موضوع النصيحة (اختياري)")
async def advice(interaction: discord.Interaction, topic: str = "الحياة"):
    await interaction.response.defer()
    result = ask_groq(
        f"اديني نصيحة حكيمة عن: {topic}",
        system="أنت Lore، كيان حكيم وغامض. اديه نصيحة عميقة ومثيرة للتفكير بأسلوبك الغامض."
    )
    embed = discord.Embed(description=f"💡 *{result}*", color=0xa78bfa)
    embed.set_footer(text="من حكمة Lore 👁️")
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════════
#  /translate
# ═══════════════════════════════════════════
@client.tree.command(name="translate", description="Lore يترجم أي نص")
@app_commands.describe(text="النص اللي عايز تترجمه", language="اللغة المطلوبة مثلاً: English, French, Spanish")
async def translate(interaction: discord.Interaction, text: str, language: str):
    await interaction.response.defer()
    result = ask_groq(
        f"ترجم هذا النص إلى {language}: {text}",
        system="أنت مترجم محترف. ترجم النص المطلوب بدقة فقط بدون أي كلام إضافي."
    )
    embed = discord.Embed(
        title=f"🌍 ترجمة إلى {language}",
        description=f"**الأصل:** {text}\n\n**الترجمة:** {result}",
        color=0x7c3aed
    )
    await interaction.followup.send(embed=embed)

client.run(DISCORD_TOKEN)
