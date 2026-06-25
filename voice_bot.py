import discord
import asyncio
import json
import os

BOT_TOKEN    = os.environ.get("TOKEN")
GUILD_ID     = 1334601401900204044
VOICE_CH_ID  = 1351272912002224148

# Temp voice settings
TEMP_VOICE_CHANNEL_NAME = "Create-temp-voice🎤"
TEMP_VOICE_CMDS_CHANNEL = "✨・temp-⇜vc-⇜cmnds"
TEMP_VOICE_IMAGE = "https://cdn.discordapp.com/attachments/1350613186017230951/1518072231006179411/ChatGPT_Image_Jun_21_2026_02_23_19_AM.png?ex=6a3e8530&is=6a3d33b0&hm=583d5aa5424901c50a2d36c239f5404b11b1f27b903171caeee8ea380b7dbdd0&"

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

ROLES_CHANNEL_NAME = "🔦・self-role"
IDS_FILE = "message_ids.json"

intents = discord.Intents.default()
intents.voice_states = True
intents.reactions = True
intents.members = True
intents.guilds = True
intents.guild_messages = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

voice_client = None
reaction_message_id = None
gender_message_id = None

# Store temp channels: {voice_channel_id: {"owner": member_id, "text_msg": message}}
temp_channels = {}


def save_ids():
    with open(IDS_FILE, "w") as f:
        json.dump({"reaction": reaction_message_id, "gender": gender_message_id}, f)


def load_ids():
    global reaction_message_id, gender_message_id
    if os.path.exists(IDS_FILE):
        with open(IDS_FILE) as f:
            data = json.load(f)
            reaction_message_id = data.get("reaction")
            gender_message_id = data.get("gender")
            print(f"Loaded message IDs: reaction={reaction_message_id}, gender={gender_message_id}")


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


async def setup_reaction_roles():
    global reaction_message_id, gender_message_id
    await client.wait_until_ready()

    guild = client.get_guild(GUILD_ID)
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
            gender_message_id = None

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


# ── Temp Voice Buttons ──────────────────────────────────────────────────────

class TempVoiceView(discord.ui.View):
    def __init__(self, owner_id, voice_channel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.voice_channel = voice_channel

    def is_owner(self, interaction):
        return interaction.user.id == self.owner_id

    @discord.ui.button(label="🔒 Lock", style=discord.ButtonStyle.danger, custom_id="tv_lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("Only the channel owner can do this!", ephemeral=True)
        await self.voice_channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Channel locked!", ephemeral=True)

    @discord.ui.button(label="🔓 Unlock", style=discord.ButtonStyle.success, custom_id="tv_unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("Only the channel owner can do this!", ephemeral=True)
        await self.voice_channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Channel unlocked!", ephemeral=True)

    @discord.ui.button(label="✏️ Rename", style=discord.ButtonStyle.primary, custom_id="tv_rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("Only the channel owner can do this!", ephemeral=True)
        await interaction.response.send_modal(RenameModal(self.voice_channel))

    @discord.ui.button(label="👥 Set Limit", style=discord.ButtonStyle.secondary, custom_id="tv_limit")
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("Only the channel owner can do this!", ephemeral=True)
        await interaction.response.send_modal(LimitModal(self.voice_channel))

    @discord.ui.button(label="🗑️ Delete", style=discord.ButtonStyle.danger, custom_id="tv_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.is_owner(interaction):
            return await interaction.response.send_message("Only the channel owner can do this!", ephemeral=True)
        await interaction.response.send_message("Deleting channel...", ephemeral=True)
        try:
            await self.voice_channel.delete()
        except Exception:
            pass


class RenameModal(discord.ui.Modal, title="Rename Your Channel"):
    name = discord.ui.TextInput(label="New Channel Name", max_length=32)

    def __init__(self, voice_channel):
        super().__init__()
        self.voice_channel = voice_channel

    async def on_submit(self, interaction: discord.Interaction):
        await self.voice_channel.edit(name=self.name.value)
        await interaction.response.send_message(f"✅ Channel renamed to **{self.name.value}**!", ephemeral=True)


class LimitModal(discord.ui.Modal, title="Set Member Limit"):
    limit = discord.ui.TextInput(label="Member Limit (0 = unlimited)", max_length=2)

    def __init__(self, voice_channel):
        super().__init__()
        self.voice_channel = voice_channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.limit.value)
            await self.voice_channel.edit(user_limit=val)
            await interaction.response.send_message(f"✅ Limit set to **{val}**!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number!", ephemeral=True)


async def send_temp_voice_interface(guild, member, voice_channel):
    cmds_channel = voice_channel

    embed = discord.Embed(
        title=f"🎤 {member.display_name}'s Channel",
        description=(
            f"**Channel:** {voice_channel.mention}\n"
            f"**Owner:** {member.mention}\n\n"
            "Use the buttons below to manage your temp voice channel!"
        ),
        color=0x5865F2
    )
    embed.set_image(url=TEMP_VOICE_IMAGE)
    embed.set_footer(text="Channel will be deleted when everyone leaves")

    view = TempVoiceView(owner_id=member.id, voice_channel=voice_channel)
    msg = await cmds_channel.send(embed=embed, view=view)
    return msg


# ── Events ──────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    load_ids()
    client.loop.create_task(keep_in_voice())
    client.loop.create_task(setup_reaction_roles())


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

    # User joined the "Create temp voice" channel
    if after.channel and after.channel.name == TEMP_VOICE_CHANNEL_NAME:
        category = after.channel.category
        new_channel = await guild.create_voice_channel(
            name=f"🎤 {member.display_name}'s VC",
            category=category,
            user_limit=0
        )
        await member.move_to(new_channel)
        msg = await send_temp_voice_interface(guild, member, new_channel)
        temp_channels[new_channel.id] = {"owner": member.id, "msg": msg}
        print(f"Created temp VC for {member.name}")

    # User left a temp channel — delete if empty
    if before.channel and before.channel.id in temp_channels:
        if len(before.channel.members) == 0:
            data = temp_channels.pop(before.channel.id, None)
            try:
                await before.channel.delete()
                print(f"Deleted empty temp VC: {before.channel.name}")
            except Exception:
                pass
            if data and data.get("msg"):
                try:
                    await data["msg"].delete()
                except Exception:
                    pass


@client.event
async def on_raw_reaction_add(payload):
    if payload.user_id == client.user.id:
        return

    guild = client.get_guild(payload.guild_id)
    emoji = str(payload.emoji)
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

    guild = client.get_guild(payload.guild_id)
    emoji = str(payload.emoji)
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
