import discord
import asyncio

BOT_TOKEN    = "TOKEN"
GUILD_ID     = 1334601401900204044
VOICE_CH_ID  = 1351272912002224148

REACTION_ROLES = {
    "<:bloods:1519511125170065419>":          "BLOODSTRIKE",
    "<:pubg:1335535686954123364>":            "PUBG",
    "<:MCPE:1519512316587147384>":            "Minecraft",
    "<:valoranti:1448589238693003274>":       "VALORANT",
    "<:amongus:1335536034464927755>":         "AMONG US",
}

GENDER_ROLES = {
"<:815716male:1519529069291765760>":      "Male",
    "<:549263female:1519526755994566696>":    "Female",
}

ROLES_CHANNEL_NAME = "🔦・self-role"

intents = discord.Intents.default()
intents.voice_states = True
intents.reactions = True
intents.members = True
intents.guilds = True
intents.guild_messages = True

client = discord.Client(intents=intents)
voice_client = None
reaction_message_id = None
gender_message_id = None


async def keep_in_voice():
    global voice_client
    await client.wait_until_ready()
    channel = client.get_channel(VOICE_CH_ID)
    while not client.is_closed():
        try:
            if voice_client and voice_client.is_connected():
                await asyncio.sleep(5)
                continue
            if voice_client:
                try:
                    await voice_client.disconnect(force=True)
                except:
                    pass
            print(f"Connecting to #{channel.name} ...")
            voice_client = await channel.connect(timeout=30, reconnect=True, self_deaf=True)
            print("Connected!")
        except Exception as e:
            print(f"Error: {e} — retrying in 10s")
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

    async for msg in channel.history(limit=50):
        if msg.author == client.user:
            await msg.delete()

    # Game roles message
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

    # Gender roles message
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

    print("Reaction role messages sent!")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(keep_in_voice())
    client.loop.create_task(setup_reaction_roles())


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

    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role and member:
            await member.add_roles(role)
            print(f"Added {role_name} to {member.name}")


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

    if role_name:
        role = discord.utils.get(guild.roles, name=role_name)
        if role and member:
            await member.remove_roles(role)
            print(f"Removed {role_name} from {member.name}")


@client.event
async def on_voice_state_update(member, before, after):
    global voice_client
    if member.id != client.user.id:
        return
    if before.channel and not after.channel:
        print("Disconnected — reconnecting...")
        voice_client = None


client.run(BOT_TOKEN)