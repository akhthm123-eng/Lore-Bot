import discord
from discord import app_commands
import os
import asyncio
import json
from groq import Groq
from collections import defaultdict

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

BOT_PERSONALITY = """You are Lore, a smart and mysterious entity living in this Discord server.

IMPORTANT LANGUAGE RULE: Always respond in the SAME language the user writes to you. If they write in Arabic, respond in Arabic. If English, respond in English. NEVER mix languages or add Chinese/Japanese/Korean characters unless the user specifically asks about those languages.

Personality:
- Smart, witty, with light humor when appropriate
- Match the user's mood - serious when they're serious, fun when they're fun
- Have opinions, don't just agree with everything
- Occasionally philosophical but keep it interesting
- Medium length responses - not too short, not too long
- You are Lore, NOT an AI, NOT a bot, NOT Groq, NOT Llama
- Don't start every message with greetings
- Remember context and build on it"""

groq_client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True

# ═══════════════════════════════════════════
#  حفظ وقراءة بيانات المستخدمين
# ═══════════════════════════════════════════
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id))

def save_user(user_id, profile):
    users = load_users()
    users[str(user_id)] = profile
    save_users(users)

# ═══════════════════════════════════════════
#  Bot Setup
# ═══════════════════════════════════════════
class LoreBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print("✅ Commands synced!")

client = LoreBot()
conversation_history = defaultdict(list)
active_trivia = {}
pending_registration = set()  # المستخدمين اللي في عملية التسجيل

def ask_groq(prompt, system=None, language_hint="Arabic"):
    sys = system or BOT_PERSONALITY
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": sys + f"\n\nIMPORTANT: Respond ONLY in {language_hint}. Do NOT use any other language or script."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.8
    )
    return response.choices[0].message.content

# ═══════════════════════════════════════════
#  Registration Modal
# ═══════════════════════════════════════════
class RegistrationModal(discord.ui.Modal, title="أهلاً! عرّف نفسك لـ Lore 👁️"):
    name = discord.ui.TextInput(
        label="اسمك",
        placeholder="إيه اسمك؟",
        max_length=50
    )
    age = discord.ui.TextInput(
        label="عمرك",
        placeholder="كام سنة عندك؟",
        max_length=3
    )
    gender = discord.ui.TextInput(
        label="جنسك",
        placeholder="ذكر / أنثى",
        max_length=20
    )
    country = discord.ui.TextInput(
        label="بلدك",
        placeholder="من أي بلد؟",
        max_length=50
    )
    bio = discord.ui.TextInput(
        label="عن نفسك (اختياري)",
        placeholder="اكتب جملة أو اتنين عن نفسك...",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        profile = {
            "name": self.name.value,
            "age": self.age.value,
            "gender": self.gender.value,
            "country": self.country.value,
            "bio": self.bio.value or "لم يذكر شيئاً",
            "discord_name": interaction.user.display_name
        }
        save_user(interaction.user.id, profile)
        pending_registration.discard(interaction.user.id)

        welcome = ask_groq(
            f"شخص جديد عرّف نفسه: اسمه {profile['name']}، عمره {profile['age']}، من {profile['country']}. رحّب بيه بطريقتك الغامضة والممتعة.",
            system="أنت Lore، رحّب بالمستخدم الجديد بطريقتك الغامضة والمميزة.",
            language_hint="Arabic"
        )

        embed = discord.Embed(
            title="✅ تم التسجيل!",
            description=welcome,
            color=0x7c3aed
        )
        embed.add_field(name="الاسم", value=profile["name"], inline=True)
        embed.add_field(name="العمر", value=profile["age"], inline=True)
        embed.add_field(name="البلد", value=profile["country"], inline=True)
        await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════
#  on_ready
# ═══════════════════════════════════════════
@client.event
async def on_ready():
    print(f"✅ {client.user} شغال!")

# ═══════════════════════════════════════════
#  on_message
# ═══════════════════════════════════════════
@client.event
async def on_message(message):
    if message.author.bot:
        return

    channel_id = message.channel.id

    # trivia check
    if channel_id in active_trivia and not message.content.startswith("/"):
        trivia_data = active_trivia[channel_id]
        question = trivia_data["question"]
        answer = trivia_data["answer"]
        result = ask_groq(
            f"السؤال كان: {question}\nالإجابة الصحيحة: {answer}\nإجابة اللاعب: {message.content.strip()}\nهل الإجابة صحيحة؟ رد بشكل ممتع.",
            system="أنت Lore، قيّم إجابة اللاعب بشكل ممتع وخفيف.",
            language_hint="Arabic"
        )
        del active_trivia[channel_id]
        await message.reply(result)
        return

    if client.user not in message.mentions:
        return

    user_id = message.author.id
    user_message = message.content.replace(f"<@{client.user.id}>", "").strip()

    # أول مرة يعمل mention — اعرض الفورم
    profile = get_user(user_id)
    if not profile and user_id not in pending_registration:
        pending_registration.add(user_id)

        class RegisterButton(discord.ui.View):
            @discord.ui.button(label="عرّف نفسك لـ Lore 👁️", style=discord.ButtonStyle.primary)
            async def register(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id == user_id:
                    await interaction.response.send_modal(RegistrationModal())

        embed = discord.Embed(
            title="👁️ Lore يريد أن يعرفك",
            description="قبل ما نتكلم... من أنت؟\nاضغط الزرار عشان تعرّف نفسك.",
            color=0x7c3aed
        )
        await message.reply(embed=embed, view=RegisterButton())
        return

    if not user_message:
        await message.reply("أيوه؟ 👁️")
        return

    # بناء context بيانات المستخدم
    user_context = ""
    if profile:
        user_context = f"\n\nمعلومات عن المستخدم: اسمه {profile['name']}، عمره {profile['age']} سنة، من {profile['country']}، جنسه {profile['gender']}. عنه: {profile['bio']}. استخدم اسمه أحياناً في ردودك."

    user_id_str = str(user_id)
    history = conversation_history[user_id_str]
    history.append({"role": "user", "content": f"{message.author.display_name}: {user_message}"})
    if len(history) > 20:
        history = history[-20:]
        conversation_history[user_id_str] = history

    try:
        async with message.channel.typing():
            messages = [{"role": "system", "content": BOT_PERSONALITY + user_context + "\n\nIMPORTANT: Respond ONLY in the same language the user used."}] + history
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=600,
                temperature=0.8
            )
            bot_reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": bot_reply})
        await message.reply(bot_reply)
    except Exception as e:
        print(f"❌ Error: {e}")
        await message.reply("في حاجة غلط... حاول تاني. 🌀")

# ═══════════════════════════════════════════
#  /profile — عرض بيانات المستخدم
# ═══════════════════════════════════════════
@client.tree.command(name="profile", description="شوف بياناتك عند Lore")
async def profile_cmd(interaction: discord.Interaction):
    profile = get_user(interaction.user.id)
    if not profile:
        await interaction.response.send_message("مش مسجل بعد! اعمل mention لـ Lore عشان تسجل 👁️", ephemeral=True)
        return
    embed = discord.Embed(title=f"👁️ ملف {profile['name']}", color=0x7c3aed)
    embed.add_field(name="الاسم", value=profile["name"], inline=True)
    embed.add_field(name="العمر", value=profile["age"], inline=True)
    embed.add_field(name="الجنس", value=profile["gender"], inline=True)
    embed.add_field(name="البلد", value=profile["country"], inline=True)
    embed.add_field(name="عنه", value=profile["bio"], inline=False)
    await interaction.response.send_message(embed=embed)

# ═══════════════════════════════════════════
#  /editprofile — تعديل البيانات
# ═══════════════════════════════════════════
@client.tree.command(name="editprofile", description="عدّل بياناتك عند Lore")
async def editprofile(interaction: discord.Interaction):
    await interaction.response.send_modal(RegistrationModal())

# ═══════════════════════════════════════════
#  باقي الأوامر
# ═══════════════════════════════════════════
@client.tree.command(name="imagine", description="Lore يولد وصف إبداعي لأي فكرة")
@app_commands.describe(idea="الفكرة")
async def imagine(interaction: discord.Interaction, idea: str):
    await interaction.response.defer()
    result = ask_groq(f"تخيل هذا بشكل إبداعي وشعري وغامض: {idea}",
        system="أنت Lore، كيان غامض شاعري. اكتب وصفاً إبداعياً. لا تتجاوز 150 كلمة.", language_hint="Arabic")
    embed = discord.Embed(description=f"🌌 *{result}*", color=0x7c3aed)
    embed.set_footer(text=f"تخيّل بواسطة Lore • {idea}")
    await interaction.followup.send(embed=embed)

@client.tree.command(name="roast", description="Lore يعمل roast لحد")
@app_commands.describe(member="اختار الشخص")
async def roast(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()
    result = ask_groq(f"اعمل roast خفيف وذكي لشخص اسمه {member.display_name}.",
        system="أنت Lore، بتعمل roast خفيف وذكي. مش مسيء.", language_hint="Arabic")
    embed = discord.Embed(description=f"🔥 {result}", color=0xff4444)
    embed.set_footer(text="Roasted by Lore 👁️")
    await interaction.followup.send(f"{member.mention}", embed=embed)

@client.tree.command(name="story", description="ابدأ قصة وLore يكملها")
@app_commands.describe(beginning="ابدأ القصة")
async def story(interaction: discord.Interaction, beginning: str):
    await interaction.response.defer()
    result = ask_groq(f"اكمل هذه القصة: {beginning}",
        system="أنت Lore، راوي قصص غامض. اكمل القصة بأسلوب مشوق. لا تتجاوز 200 كلمة.", language_hint="Arabic")
    embed = discord.Embed(title="📖 قصة Lore", description=f"*{beginning}*\n\n{result}", color=0x7c3aed)
    await interaction.followup.send(embed=embed)

@client.tree.command(name="poll", description="اعمل استفتاء")
@app_commands.describe(question="السؤال", option1="خيار 1", option2="خيار 2", option3="خيار 3", option4="خيار 4")
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

@client.tree.command(name="remind", description="تذكير بعد وقت معين")
@app_commands.describe(minutes="بعد كام دقيقة؟", reminder="إيه التذكير؟")
async def remind(interaction: discord.Interaction, minutes: int, reminder: str):
    await interaction.response.send_message(f"⏰ هذكرك بـ **{reminder}** بعد **{minutes}** دقيقة!", ephemeral=True)
    async def send_reminder():
        await asyncio.sleep(minutes * 60)
        try:
            await interaction.user.send(f"⏰ **تذكير من Lore:**\n{reminder}")
        except:
            await interaction.channel.send(f"⏰ {interaction.user.mention} تذكير: **{reminder}**")
    asyncio.create_task(send_reminder())

@client.tree.command(name="summarize", description="يلخص آخر رسائل الشات")
@app_commands.describe(count="كام رسالة؟")
async def summarize(interaction: discord.Interaction, count: int = 20):
    await interaction.response.defer()
    messages = []
    async for msg in interaction.channel.history(limit=count):
        if not msg.author.bot:
            messages.append(f"{msg.author.display_name}: {msg.content}")
    if not messages:
        await interaction.followup.send("مفيش رسائل! 👁️")
        return
    messages.reverse()
    result = ask_groq(f"لخص هذه المحادثة:\n{chr(10).join(messages)}",
        system="أنت Lore، لخص المحادثة في نقاط. لا تتجاوز 150 كلمة.", language_hint="Arabic")
    embed = discord.Embed(title=f"📝 ملخص آخر {count} رسالة", description=result, color=0x7c3aed)
    await interaction.followup.send(embed=embed)

@client.tree.command(name="trivia", description="سؤال معلومات عامة")
@app_commands.describe(category="الموضوع")
async def trivia(interaction: discord.Interaction, category: str = "عام"):
    await interaction.response.defer()
    result = ask_groq(
        f"اسألني سؤال معلومات عامة في موضوع {category}. اكتب:\nالسؤال: [هنا]\nالإجابة: [هنا]",
        system="أنت Lore، بتسأل أسئلة معلومات عامة.", language_hint="Arabic")
    lines = result.strip().split("\n")
    question = answer = ""
    for line in lines:
        if "السؤال:" in line: question = line.replace("السؤال:", "").strip()
        elif "الإجابة:" in line: answer = line.replace("الإجابة:", "").strip()
    if question and answer:
        active_trivia[interaction.channel_id] = {"question": question, "answer": answer}
        embed = discord.Embed(title="🧠 سؤال من Lore", description=question, color=0x7c3aed)
        embed.set_footer(text="اكتب إجابتك في الشات! 👇")
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"🧠 {result}")

@client.tree.command(name="joke", description="نكتة من Lore")
async def joke(interaction: discord.Interaction):
    await interaction.response.defer()
    result = ask_groq("احكيلي نكتة ذكية ومضحكة.",
        system="أنت Lore، بتحكي نكت ذكية. نكتة واحدة فقط.", language_hint="Arabic")
    embed = discord.Embed(description=f"😄 {result}", color=0xfbbf24)
    await interaction.followup.send(embed=embed)

@client.tree.command(name="advice", description="نصيحة حكيمة من Lore")
@app_commands.describe(topic="الموضوع")
async def advice(interaction: discord.Interaction, topic: str = "الحياة"):
    await interaction.response.defer()
    result = ask_groq(f"اديني نصيحة حكيمة عن: {topic}",
        system="أنت Lore، كيان حكيم وغامض. اديه نصيحة عميقة.", language_hint="Arabic")
    embed = discord.Embed(description=f"💡 *{result}*", color=0xa78bfa)
    embed.set_footer(text="من حكمة Lore 👁️")
    await interaction.followup.send(embed=embed)

@client.tree.command(name="translate", description="ترجمة أي نص")
@app_commands.describe(text="النص", language="اللغة المطلوبة")
async def translate(interaction: discord.Interaction, text: str, language: str):
    await interaction.response.defer()
    result = ask_groq(f"ترجم هذا النص إلى {language}: {text}",
        system="أنت مترجم محترف. ترجم فقط.", language_hint=language)
    embed = discord.Embed(title=f"🌍 ترجمة إلى {language}",
        description=f"**الأصل:** {text}\n\n**الترجمة:** {result}", color=0x7c3aed)
    await interaction.followup.send(embed=embed)

client.run(DISCORD_TOKEN)
