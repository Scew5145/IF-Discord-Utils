import discord
from discord import app_commands
from discord.utils import get
from datetime import datetime as dt
from datetime import timedelta
import heapq
import random
import os
import json

# from config import TOKEN, GUILD_ID, ROLE_ID
print(os.environ)
TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["DISCORD_GUILD_ID"])
ROLE_ID = int(os.environ["DISCORD_ROLE"])

intents = discord.Intents.all()
intents.messages = True
intents.members = True
intents.presences = True


class FeebasClient(discord.Client):
    synced = False

    async def on_ready(self):
        print("Feebas started")
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=GUILD_ID))
            self.synced = True
        print(f"Logged in as {self.user}")


feebas = FeebasClient(intents=intents)
tree = app_commands.CommandTree(feebas)
sample_count = 7
recently_used_channels = {}
feedback_cooldown = timedelta(hours=6)


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"tag {sample_count} random members with the feedback giver role")
async def feedbackpls(interaction: discord.Interaction):
    guild = interaction.guild
    role = get(guild.roles, id=ROLE_ID)

    update_allowed_channels()

    thread = get(guild.threads, id=interaction.channel_id)
    if thread is not None and thread.owner_id != interaction.user.id:
        await interaction.response.send_message("Only the owner of the spritework thread can use this command.", ephemeral=True)
        return

    if thread is not None and thread.id in recently_used_channels:
        remaining_cooldown = recently_used_channels[thread.id] - dt.now()
        output_string = f"This command has a cooldown in the same thread of {str(feedback_cooldown)}. Please wait {str(remaining_cooldown)}"
        await interaction.response.send_message(output_string, ephemeral=True)
        return

    allowed_ping_statuses = [discord.Status.online, discord.Status.idle]
    ids = [member.id for member in role.members]
    # splitting requests for the sake of the API call
    split_ids = list(chunk_array(ids, 100))
    feedback_users = []
    for group in split_ids:
        feedback_users += (await guild.query_members(user_ids=group, presences=True))
    online_users = [member for member in feedback_users if member.status in allowed_ping_statuses]
    if interaction.user in online_users:
        online_users.remove(interaction.user)
    if sample_count <= len(online_users):
        sample = random.sample(online_users, sample_count)
    else:
        sample = online_users

    # Used this to check statuses, and it looks like sometimes discord will cache status on the client, but these seem to be accurate most of the time
    # print([(user.name, user.status) for user in sample])
    tags = [f"<@{member.id}>" for member in sample]
    joined_tags = '\n'.join(tags)
    await interaction.response.send_message(f"THESE PEOPLE HAVE BEEN (forcefully) RECRUITED TO GIVE YOU FEEDBACK:\n{joined_tags}\n (feedbackers can get the Sprite Feedback Giver role removed if they don't want these pings)", ephemeral=False)
    # add it to recently_used_channels only after send_message is called, just in case it errors out (which is a thing)
    if thread is not None:
        recently_used_channels[thread.id] = dt.now() + feedback_cooldown


def update_allowed_channels():
    now = dt.now()
    output_array = []
    for channel in recently_used_channels:
        timestamp = recently_used_channels[channel]
        if timestamp < now:
            output_array.append(channel)
    for channel in output_array:
        del recently_used_channels[channel]


top_count = 15
DISCORD_GALLERY_ID = int(os.environ["DISCORD_GALLERY_ID"])


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"gather the top {top_count} sprites from the past week",)
async def get_top_sprites(interaction: discord.Interaction):
    gallery = interaction.guild.get_channel(int(DISCORD_GALLERY_ID))
    now = dt.now()
    week_ago = now - timedelta(days=7)
    top_sprites = list()
    tiebreak_counter = 0
    message_counter = 0
    await interaction.response.send_message("This operation will take a while! Check back in this channel in half an hour.", ephemeral=False)
    async for message in gallery.history(after=week_ago, limit=None):
        message_counter += 1
        if message_counter % 500 == 0:
            await interaction.channel.send(f"Parsed {message_counter} gallery posts")
        reaction_ids = set()
        # api usage optimization: if the sum of all reaction.count is < the X most reacted to sprite,
        # we know that we can skip this message for the top X number sprites
        reaction_sum = sum(reaction.count for reaction in message.reactions)
        if len(top_sprites) == top_count and reaction_sum < top_sprites[0][0]:
            continue
        for reaction in message.reactions:
            try:
                async for user in reaction.users():
                    reaction_ids.add(user.id)
            except discord.errors.HTTPException as e:
                if e.code == 10014:
                    print(f"failed to find emoji for message: {message}. Skipping")
                    continue
                else:
                    raise e

        heapq.heappush(top_sprites, (len(reaction_ids), tiebreak_counter, message))
        if len(top_sprites) > top_count:
            heapq.heappop(top_sprites)
        tiebreak_counter += 1

    print([(item[2].content, item[0]) for item in top_sprites])
    output_message = ""
    output_largest = heapq.nlargest(top_count, top_sprites, key=lambda x: x[0])
    output_messages = []
    for i in range(len(output_largest)):
        data_text = output_largest[i][2].content.replace("<#", "")
        data_text = data_text.replace(">", "")
        line = f"{i + 1}: {data_text} | {output_largest[i][2].jump_url} | Unique Reactions: {output_largest[i][0]}"
        if len(line) + len(output_message) >= 2000:
            output_messages.append(output_message)
            output_message = line + "\n"
        else:
            output_message += line + "\n"
    output_messages.append(output_message)

    for final_output_message in output_messages:
        await interaction.channel.send(final_output_message)


def chunk_array(in_list, n):
    for i in range(0, len(in_list), n):
        yield in_list[i:i + n]


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"Debug Command: print thread timeouts")
async def print_thread_cooldowns(interaction: discord.Interaction):
    output_message = ""
    output_messages = []
    for channel in recently_used_channels:
        line = f"<#{channel}>: {recently_used_channels[channel] - dt.now()}"
        if len(line) + len(output_message) >= 2000:
            output_messages.append(output_message)
            output_message = line + "\n"
        else:
            output_message += line + "\n"

    output_messages.append(output_message)
    if len(output_messages) == 1 and output_message == "":
        await interaction.response.send_message("No threads on cooldown atm", ephemeral=False)
        return
    sent_response = False
    for final_output_message in output_messages:
        if final_output_message == "":
            continue
        if not sent_response:
            await interaction.response.send_message(final_output_message, ephemeral=False)
            sent_response = True
        else:
            await interaction.channel.send(final_output_message)


# Feedbacker inactivity tracker
FEEDBACKERS_LAST_RESPONSE_TIME = 7  # Time to warn users about inactivity (days)
TRACKED_RESPONSE_TIME = 30  # Number of days to pull feedback bot responses from (days)
FEEDBACKER_UPDATE_RATE = 5 # How often to pull the feedbacker response list (minutes)

# id of the spritework channel
DISCORD_SPRITEWORK_ID = int(os.environ["DISCORD_SPRITEWORK_ID"])

# User response times: Dict pointing user id --> response object.
# response object should look like this:
# {"latestReply": timestamp (or none), "pingCount": int, "responseCount": int}
user_response_times = {}
last_update = None


def get_feebas_responders(guild, feebas_message):
    thread = get(guild.threads, id=feebas_message.channel_id)
    responsive_mentions = []
    # no limit here because spritework threads are usually short. May need to limit/chunk if too expensive api wise
    thread_message_iter = thread.history(after=feebas_message.created_at)
    for thread_message in thread_message_iter:
        if len(responsive_mentions) == len(feebas_message.mentions):
            break
        if thread_message.author in feebas_message.mentions:
            responsive_mentions.append(thread_message.author)
    return responsive_mentions


async def update_feedbacker_times(guild, feedbacker_role, force=False):
    global last_update, FEEDBACKER_UPDATE_RATE
    now = dt.now()
    if not force and last_update is not None and last_update > dt.date(now - timedelta(minutes=FEEDBACKER_UPDATE_RATE)):
        print(f"Updated feedback list @ {last_update} - not updating again until {FEEDBACKER_UPDATE_RATE} minutes have passed")
        return

    last_update = now
    ids = [member.id for member in feedbacker_role.members]
    # Always fully reset the user response time dict - it's not saved between runs atm anyway
    user_response_times.clear()
    for uid in ids:
        user_response_times[uid] = {'latestReply': None,
                                    'pingCount': 0,
                                    'responseCount': 0}

    channel = guild.get_channel(DISCORD_SPRITEWORK_ID)
    start_date = now - timedelta(days=FEEDBACKERS_LAST_RESPONSE_TIME)
    print(f"Pulling active threads. Count: {len(channel.threads)}")
    for thread in channel.threads:
        feebas_messages = await thread.history(after=start_date).find(lambda m: m.author.id == feebas.user.id)
        for message in feebas_messages:
            responders = get_feebas_responders(guild, message)
            for feedbacker in message.mentions:
                user_response_times[feedbacker.id]['latestReply'] = message.created_at
                user_response_times[feedbacker.id]['pingCount'] += 1
                if feedbacker in responders:
                    user_response_times[feedbacker.id]['responseCount'] += 1
    # Have to pull archived threads too, just in case an added to gallery item was
    print("Finished pulling active threads. Searching archive...")
    async for thread in channel.archived_threads(limit=5000):
        feebas_messages = await thread.history(after=start_date).find(lambda m: m.author.id == feebas.user.id)
        for message in feebas_messages:
            responders = get_feebas_responders(guild, message)
            for feedbacker in message.mentions:
                user_response_times[feedbacker.id]['latestReply'] = message.created_at
                user_response_times[feedbacker.id]['pingCount'] += 1
                if feedbacker in responders:
                    user_response_times[feedbacker.id]['responseCount'] += 1


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"Debug Command - Update feedbackers now")
async def force_update_feedbackers(interaction: discord.Interaction):
    guild = interaction.guild
    role = get(guild.roles, id=ROLE_ID)
    await update_feedbacker_times(guild, role, force=True)
    output_string = json.dumps(user_response_times, indent=2)
    print(output_string)


#@tree.command(guild=discord.Object(id=GUILD_ID), description=f"Audit Command - checks for users over {FEEDBACKERS_LAST_RESPONSE_TIME} days who haven't responded to a feedback ping")
#async def find_inactive_feedbackers(interaction: discord.Interaction):
#
#    guild = interaction.guild
#    role = get(guild.roles, id=ROLE_ID)
#    await update_feedbacker_times(guild, role)


feebas.run(TOKEN)

