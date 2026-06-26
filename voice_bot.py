import discord
import asyncio
import json
import os
from discord.ui import Button, View

BOT_TOKEN    = os.environ.get("TOKEN")
GUILD_ID     = 1334601401900204044
VOICE_CH_ID  = 1351272912002224148

REACTION_ROLES = {
    "<:bloods:1519511125170065419>":       "BLOODSTRIKE",
    "<:pubg:1335535686954123364>":         "PUBG",
    "<:MCPE:1519512316587147384>":         "Minecraft",
    "<:valoranti:1448589238693003274>":    "VALORANT",
    "<:amongus:1335536034464927755>":      "AMONG US",
}

GENDER_ROLES = {
    "<:815716male:1519529069291765760>":   "Male",
    "<:549263female:1519526755994566696>": "Female",
}

ROLES_CHANNEL_NAME    = "🔦・self-role"
WELCOME_CHANNEL_NAME  = "👋・welcome"
VERIFY_CHANNEL_NAME   = "✅・verification"
RULES_CHANNEL_NAME    = "📜・rules"
VERIFIED_ROLE_NAME    = "Verified"
BANNER_URL            = "https://cdn.discordapp.com/attachments/1334601402546126863/1519865912314953750/Screenshot_2026-06-25_024608.png?ex=6a3f1cef&is=6a3dcb6f&hm=58867e65359fbbbc21ed2ef8799eac1c2bad91e6e3cc7f2977eab1216e62d428&"
IDS_FILE              = "message_ids.json"

intents = discord.Intents.default()
intents.voice_states   = True
intents.reactions      = True
intents.members        = True
intents.guilds         = True
intents.guild_messages = True

client = discord.Client(intents=intents)
voice_client = None
reaction_message_id = None
gender_message_id   = None


def save_ids():
    with open(IDS_FILE, "w") as f:
        json.dump({"reaction": reaction_message_id, "gender": gender_message_id}, f)


def load_ids():
    global reaction_message_id, gender_message_id
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE) as f:
            data = json.load(f)
            reaction_message_id = data.get("reaction")
            gender_message_id   = data.get("gender")
            print(f"Loaded message IDs: reaction={reaction_message_id}, gender={gender_message_id}")


# ── Verify button ─────────────────────────────────────────────────────────────

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Verify", style=discord.ButtonStyle.success, custom_id="verify_button")
    async def verify(self, interaction: discord.Interaction, button: Button):
        guild  = interaction.guild
        member = interaction.user
        role   = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        if role is None:
            await interaction.response.send_message("❌ Verified role not found! Ask an admin to create it.", ephemeral=True)
            return
        if role in member.roles:
            await interaction.response.send_message("✅ You are already verified!", ephemeral=True)
            return
        await member.add_roles(role)
        await interaction.response.send_message("✅ You have been verified! Welcome to the server!", ephemeral=True)
        print(f"Verified {member.name}")


async def setup_verify_channel():
    await client.wait_until_ready()
    guild   = client.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.text_channels, name=VERIFY_CHANNEL_NAME)
    if channel is None:
        print(f"Could not find channel: {VERIFY_CHANNEL_NAME}")
        return

    async for msg in channel.history(limit=20):
        if msg.author == client.user:
            await msg.delete()

    embed = discord.Embed(
        title="✅ Verification",
        description="Click the button below to verify yourself and gain access to the server!",
        color=0x2ecc71
    )
    await channel.send(embed=embed, view=VerifyView())
    print("Verification message sent!")


# ── Rules channel ─────────────────────────────────────────────────────────────

async def setup_rules_channel():
    await client.wait_until_ready()
    guild   = client.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.text_channels, name=RULES_CHANNEL_NAME)
    if channel is None:
        print(f"Could not find channel: {RULES_CHANNEL_NAME}")
        return

    async for msg in channel.history(limit=20):
        if msg.author == client.user:
            await msg.delete()

    embed = discord.Embed(
        title="📜 Server Rules",
        description=(
            "**1. 💬 Respectful Communication**\n"
            "All members are expected to engage in respectful and polite conversation. No harassment, hate speech, or bullying will be tolerated.\n\n"
            "**2. 🚫 No Spam**\n"
            "Avoid spamming text or voice channels. This includes excessive messages, irrelevant content, and unnecessary @mentions.\n\n"
            "**3. 🔒 Respect Privacy**\n"
            "Do not share personal information about yourself or others without explicit consent. This includes addresses, phone numbers, emails, etc.\n\n"
            "**4. 📢 No Self-Promotion or Advertising**\n"
            "Unsolicited promotion of other Discord servers, social media accounts, or products is not allowed.\n\n"
            "**5. 👮 Follow Discord's Terms of Service**\n"
            "By being a member of this server, you are expected to adhere to Discord's official Terms of Service and Community Guidelines.\n\n"
            "**6. ⚠️ Consequences**\n"
            "Violating these rules may result in a warning, mute, kick, or ban, depending on the severity of the violation.\n\n"
            "**7. 📬 Report Issues**\n"
            "If you encounter any issues or have concerns, please reach out to a moderator or server admin.\n\n"
            "Welcome to our server, and let's build a great community together! 🙌"
        ),
        color=0x5865F2
    )
    await channel.send(embed=embed)
    print("Rules message sent!")


# ── Welcome message ───────────────────────────────────────────────────────────

@client.event
async def on_member_join(member):
    guild          = member.guild
    welcome_ch     = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME)
    verify_ch      = discord.utils.get(guild.text_channels, name=VERIFY_CHANNEL_NAME)
    rules_ch       = discord.utils.get(guild.text_channels, name=RULES_CHANNEL_NAME)

    if welcome_ch is None:
        return

    verify_mention = verify_ch.mention if verify_ch else "#verification"
    rules_mention  = rules_ch.mention  if rules_ch  else "#rules"

    embed = discord.Embed(
        title=f"👋 Welcome to {guild.name}, {member.name}!",
        description=(
            f"Hey {member.mention}, welcome to **{guild.name}**! 🎉\n\n"
            f"📜 Please read the rules in {rules_mention}\n"
            f"✅ Then head to {verify_mention} to verify yourself and get access!\n\n"
            f"We're happy to have you here!"
        ),
        color=0x5865F2
    )
    embed.set_image(url=BANNER_URL)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"{guild.name} • Member #{guild.member_count}")

    await welcome_ch.send(embed=embed)
    print(f"Welcomed {member.name}")


# ── Voice keep-alive ──────────────────────────────────────────────────────────

async def keep_in_voice():
    global voice_client
    await client.wait_until_ready()
    channel = client.get_channel(VOICE_CH_ID)
    if channel is None:
        print(f"Voice channel {VOICE_CH_ID} not found!")
        return
    while not client.is_closed():
        try:
            if voice_client and voice_client.is_connected():
                await asyncio.sleep(5)
                continue
            if voice_client:
                try:
                    await voice_client.disconnect(force=True)
                except Exception:
                    pass
            print(f"Connecting to #{channel.name} ...")
            voice_client = await channel.connect(timeout=30, reconnect=True, self_deaf=True)
            print("Connected to voice!")
        except Exception as e:
            print(f"Voice error: {e} — retrying in 10s")
            await asyncio.sleep(10)
        await asyncio.sleep(5)


# ── Reaction roles setup ──────────────────────────────────────────────────────

async def setup_reaction_roles():
    global reaction_message_id, gender_message_id
    await client.wait_until_ready()

    guild   = client.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.text_channels, name=ROLES_CHANNEL_NAME)

    if channel is None:
        print(f"Could not find channel: {ROLES_CHANNEL_NAME}")
        return

    if reaction_message_id and gender_message_id:
        try:
            await channel.fetch_message(reaction_message_id)
            await channel.fetch_message(gender_message_id)
            print("Reaction role messages already exist — reusing them.")
            return
        except discord.NotFound:
            print("Saved messages not found — recreating...")
            reaction_message_id = None
            gender_message_id   = None

    async for msg in channel.history(limit=50):
        if msg.author == client.user:
            await msg.delete()

    lines = ["**🎮 React to get your Game Role!**\n"]
    for emoji, role in REACTION_ROLES.items():
        lines.append(f"{emoji} → **{role}**")
    msg1 = await channel.send("\n".join(lines))
    reaction_message_id = msg1.id
    for emoji in REACTION_ROLES.keys():
        try:
            await msg1.add_reaction(emoji)
        except Exception as e:
            print(f"Could not add reaction {emoji}: {e}")

    lines2 = ["\n**⚧ React to get your Gender Role!**\n"]
    for emoji, role in GENDER_ROLES.items():
        lines2.append(f"{emoji} → **{role}**")
    msg2 = await channel.send("\n".join(lines2))
    gender_message_id = msg2.id
    for emoji in GENDER_ROLES.keys():
        try:
            await msg2.add_reaction(emoji)
        except Exception as e:
            print(f"Could not add reaction {emoji}: {e}")

    save_ids()
    print("Reaction role messages sent and IDs saved!")


# ── Events ────────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.add_view(VerifyView())
    load_ids()
    client.loop.create_task(keep_in_voice())
    client.loop.create_task(setup_reaction_roles())
    client.loop.create_task(setup_verify_channel())
    client.loop.create_task(setup_rules_channel())


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    guild     = client.get_guild(payload.guild_id)
    emoji     = str(payload.emoji)
    member    = guild.get_member(payload.user_id)

    if payload.message_id == reaction_message_id:
        role_name = REACTION_ROLES.get(emoji)
    elif payload.message_id == gender_message_id:
        role_name = GENDER_ROLES.get(emoji)
    else:
        return

    if role_name and member:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            print(f"Added '{role_name}' to {member.name}")


@client.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == client.user.id:
        return
    guild     = client.get_guild(payload.guild_id)
    emoji     = str(payload.emoji)
    member    = guild.get_member(payload.user_id)

    if payload.message_id == reaction_message_id:
        role_name = REACTION_ROLES.get(emoji)
    elif payload.message_id == gender_message_id:
        role_name = GENDER_ROLES.get(emoji)
    else:
        return

    if role_name and member:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)
            print(f"Removed '{role_name}' from {member.name}")


@client.event
async def on_voice_state_update(member, before, after):
    global voice_client
    if member.id != client.user.id:
        return
    if before.channel and not after.channel:
        print("Bot disconnected from voice — reconnecting...")
        voice_client = None


client.run(BOT_TOKEN)
