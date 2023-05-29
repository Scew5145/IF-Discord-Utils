import discord
from discord import app_commands
from discord.utils import get
from datetime import datetime as dt
from datetime import timedelta
import heapq
import random
import os

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
feedback_cooldown = timedelta(minutes=5)


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"tag {sample_count} random members with the feedback giver role")
async def feedbackpls(interaction: discord.Interaction):
    guild = interaction.guild
    role = get(guild.roles, id=ROLE_ID)

    update_allowed_channels()

    thread = get(guild.threads, id=interaction.channel_id)
    print(thread)
    if thread is not None and thread.owner_id != interaction.user.id:
        print(thread.owner_id)
        print(interaction.user.id)
        await interaction.response.send_message("Only the owner of the spritework thread can use this command.", ephemeral=True)
        return

    if thread is not None and thread.id in recently_used_channels:
        remaining_cooldown = recently_used_channels[thread.id] - dt.now()
        output_string = f"This command has a cooldown in the same thread of {str(feedback_cooldown)}. Please wait {str(remaining_cooldown)}"
        await interaction.response.send_message(output_string, ephemeral=True)
        return
    if thread is not None:
        recently_used_channels[thread.id] = dt.now() + feedback_cooldown
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
    # tags = ["bacon"]
    joined_tags = '\n'.join(tags)
    await interaction.response.send_message(f"THESE PEOPLE HAVE BEEN (forcefully) RECRUITED TO GIVE YOU FEEDBACK:\n{joined_tags}\n (feedbackers can get the Sprite Feedback Giver role removed if they don't want these pings)", ephemeral=False)


def update_allowed_channels():
    now = dt.now()
    cooldown_timestamp = now - feedback_cooldown

    for channel in recently_used_channels:
        # Python3 so we can do this safely!
        timestamp = recently_used_channels[channel]
        if timestamp < cooldown_timestamp:
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
            async for user in reaction.users():
                reaction_ids.add(user.id)

        heapq.heappush(top_sprites, (len(reaction_ids), tiebreak_counter, message))
        if len(top_sprites) > top_count:
            heapq.heappop(top_sprites)
        tiebreak_counter += 1

    print([(item[2].content, item[0]) for item in top_sprites])
    output_message = ""
    output_largest = heapq.nlargest(top_count, top_sprites, key=lambda x: x[0])
    output_messages = []
    for i in range(len(output_largest)):
        line = f"{i + 1}: {output_largest[i][2].content} | {output_largest[i][2].jump_url} | Unique Reactions: {output_largest[i][0]}"
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

feebas.run(TOKEN)

