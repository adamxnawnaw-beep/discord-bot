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
TEMP_CMND_CHANNEL     = "✨・temp-⇜vc-⇜cmnds"
CREATE_TEMP_CHANNEL   = "Create-temp-voice🎤"
TEMP_CATEGORY_NAME    = "✦ 𝓣𝓔𝓜𝓟 𝓥𝓞𝓘𝓒𝓔 ✦"
BANNER_URL            = "https://cdn.discordapp.com/attachments/1334601402546126863/1519865912314953750/Screenshot_2026-06-25_024608.png?ex=6a3f1cef&is=6a3dcb6f&hm=58867e65359fbbbc21ed2ef8799eac1c2bad91e6e3cc7f2977eab1216e62d428&"
RULES_IMAGE_URL       = "https://cdn.discordapp.com/attachments/1334601403066220657/1519875628533289030/ChatGPT_Image_Jun_26_2026_02_22_50_AM.png?ex=6a3f25fb&is=6a3dd47b&hm=53be7605bf5ea0aa19b0d7408a849a13b21748f8377e50ad2cd6c5a67013a3cc&"
TEMP_IMAGE_URL        = "https://cdn.discordapp.com/attachments/1334601401900204044/1782598824806/ChatGPT_Image_Jun_21__2026__02_23_19_AM.png"
IDS_FILE              = "message_ids.json"

intents = discord.Intents.default()
intents.voice_states   = True
intents.reactions      = True
intents.members        = True
intents.guilds         = True
intents.guild_messages = True

client = discord.Client(intents=intents)
voice_client     = None
reaction_message_id = None
gender_message_id   = None
temp_channels    = {}  # {channel_id: owner_id}


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


# ── Temp VC Control Panel ─────────────────────────────────────────────────────

class TempVCView(View):
    def __init__(self, channel_id, owner_id):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.owner_id   = owner_id

    async def check_owner(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Only the channel owner can do this!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, custom_id="vc_lock")
    async def lock(self, interaction: discord.Interaction, button: Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.response.send_message("🔒 Channel locked!", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success, custom_id="vc_unlock")
    async def unlock(self, interaction: discord.Interaction, button: Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.response.send_message("🔓 Channel unlocked!", ephemeral=True)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="vc_rename")
    async def rename(self, interaction: discord.Interaction, button: Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_message("✏️ Reply with the new name for your channel!", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel

        try:
            msg = await client.wait_for("message", check=check, timeout=30)
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.edit(name=msg.content)
                await msg.delete()
                await interaction.followup.send(f"✅ Channel renamed to **{msg.content}**!", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Timed out. Try again.", ephemeral=True)

    @discord.ui.button(label="👥 Set Limit", style=discord.ButtonStyle.secondary, custom_id="vc_limit")
    async def set_limit(self, interaction: discord.Interaction, button: Button):
        if not await self.check_owner(interaction):
            return
        await interaction.response.send_message("👥 Reply with the max number of members (0 = unlimited)!", ephemeral=True)

        def check(m):
            return m.author.id == interaction.user.id and m.channel == interaction.channel

        try:
            msg = await client.wait_for("message", check=check, timeout=30)
            limit = int(msg.content)
            channel = interaction.guild.get_channel(self.channel_id)
            if channel:
                await channel.edit(user_limit=limit)
                await msg.delete()
                await interaction.followup.send(f"✅ Member limit set to **{limit}**!", ephemeral=True)
        except (asyncio.TimeoutError, ValueError):
            await interaction.followup.send("⏱️ Timed out or invalid number. Try again.", ephemeral=True)

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger, custom_id="vc_delete")
    async def delete(self, interaction: discord.Interaction, button: Button):
        if not await self.check_owner(interaction):
            return
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await interaction.response.send_message("🗑️ Deleting your channel...", ephemeral=True)
            await channel.delete()
            if self.channel_id in temp_channels:
                del temp_channels[self.channel_id]


# ── Temp VC tutorial message ──────────────────────────────────────────────────

async def setup_temp_tutorial():
    await client.wait_until_ready()
    guild   = client.get_guild(GUILD_ID)
    channel = discord.utils.get(guild.text_channels, name=TEMP_CMND_CHANNEL)
    if channel is None:
        print(f"Could not find channel: {TEMP_CMND_CHANNEL}")
        return

    async for msg in channel.history(limit=20):
        if msg.author == client.user:
            await msg.delete()

    embed = discord.Embed(
        title="🎤 Temp Voice Channels",
        description=(
            "**How to use:**\n\n"
            "◆ Join **Create-temp-voice🎤** to create your own VC\n"
            "◆ A private channel will be created for you\n"
            "◆ Use the buttons in your VC to manage it\n\n"
            "**Controls:**\n"
            "🔒 **Lock** — Stop others from joining\n"
            "🔓 **Unlock** — Allow others to join\n"
            "✏️ **Rename** — Change your channel name\n"
            "👥 **Set Limit** — Set max members\n"
            "🗑️ **Delete** — Delete your channel\n\n"
            "Your channel auto-deletes when everyone leaves!"
        ),
        color=0x5865F2
    )
    embed.set_image(url=TEMP_IMAGE_URL)
    await channel.send(embed=embed)
    print("Temp VC tutorial sent!")


# ── Voice state — temp VC logic ───────────────────────────────────────────────

@client.event
async def on_voice_state_update(member, before, after):
    global voice_client

    # Keep bot in voice
    if member.id == client.user.id:
        if before.channel and not after.channel:
            print("Bot disconnected from voice — reconnecting...")
            voice_client = None
        return

    guild = member.guild

    # Someone joined the create channel
    if after.channel and after.channel.name == CREATE_TEMP_CHANNEL:
        category = discord.utils.get(guild.categories, name=TEMP_CATEGORY_NAME)
        new_channel = await guild.create_voice_channel(
            name=f"🎤 {member.display_name}'s VC",
            category=category,
            user_limit=0
        )
        temp_channels[new_channel.id] = member.id
        await member.move_to(new_channel)

        # Find the text commands channel and send control panel
        cmnd_channel = discord.utils.get(guild.text_channels, name=TEMP_CMND_CHANNEL)
        if cmnd_channel:
            embed = discord.Embed(
                title=f"🎤 {member.display_name}'s VC Controls",
                description=(
                    f"Hey {member.mention}! Your temp VC has been created.\n"
                    "Use the buttons below to manage it!\n\n"
                    "🔒 **Lock** — Stop others from joining\n"
                    "🔓 **Unlock** — Allow others to join\n"
                    "✏️ **Rename** — Change your channel name\n"
                    "👥 **Set Limit** — Set max members\n"
                    "🗑️ **Delete** — Delete your channel"
                ),
                color=0x2ecc71
            )
            embed.set_image(url=TEMP_IMAGE_URL)
            await cmnd_channel.send(
                content=member.mention,
                embed=embed,
                view=TempVCView(new_channel.id, member.id)
            )
        print(f"Created temp VC for {member.display_name}")

    # Someone left a temp channel — delete if empty
    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            del temp_channels[before.channel.id]
            await before.channel.delete()
            print(f"Deleted empty temp VC: {before.channel.name}")


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
            await interaction.response.send_message("❌ Verified role not found!", ephemeral=True)
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
    embed.set_image(url=RULES_IMAGE_URL)
    await channel.send(embed=embed)
    print("Rules message sent!")


# ── Welcome message ───────────────────────────────────────────────────────────

@client.event
async def on_member_join(member):
    guild      = member.guild
    welcome_ch = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME)
    verify_ch  = discord.utils.get(guild.text_channels, name=VERIFY_CHANNEL_NAME)
    rules_ch   = discord.utils.get(guild.text_channels, name=RULES_CHANNEL_NAME)

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
        return

    if reaction_message_id and gender_message_id:
        try:
            await channel.fetch_message(reaction_message_id)
            await channel.fetch_message(gender_message_id)
            print("Reaction role messages already exist — reusing them.")
            return
        except discord.NotFound:
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
    print("Reaction role messages sent!")


# ── on_ready ──────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.add_view(VerifyView())
    load_ids()
    client.loop.create_task(keep_in_voice())
    client.loop.create_task(setup_reaction_roles())
    client.loop.create_task(setup_verify_channel())
    client.loop.create_task(setup_rules_channel())
    client.loop.create_task(setup_temp_tutorial())


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return
    guild  = client.get_guild(payload.guild_id)
    emoji  = str(payload.emoji)
    member = guild.get_member(payload.user_id)

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
    guild  = client.get_guild(payload.guild_id)
    emoji  = str(payload.emoji)
    member = guild.get_member(payload.user_id)

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


client.run(BOT_TOKEN)
