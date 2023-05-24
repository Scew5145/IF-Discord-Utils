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


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"tag {sample_count} random members with the feedback giver role")
async def feedbackpls(interaction: discord.Interaction):
    guild = interaction.guild
    role = get(guild.roles, id=ROLE_ID)

    sample = []
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


top_count = 15
DISCORD_GALLERY_ID = int(os.environ["DISCORD_GALLERY_ID"])


@tree.command(guild=discord.Object(id=GUILD_ID), description=f"gather the top {top_count} sprites from the past week",)
async def get_top_sprites(interaction: discord.Interaction):
    gallery = interaction.guild.get_channel(int(DISCORD_GALLERY_ID))
    now = dt.now()
    week_ago = now - timedelta(days=7)
    top_sprites = list()
    tiebreak_counter = 0
    await interaction.response.defer(ephemeral=False)
    async for message in gallery.history(after=week_ago, limit=None):
        reaction_ids = set()
        print(f"{message.content} \n done")
        # api usage optimization: if the sum of all reaction.count is < the X most reacted to sprite,
        # we know that we can skip this message for the top X number sprites
        reaction_sum = sum(reaction.count for reaction in message.reactions)
        if len(top_sprites) == top_count and reaction_sum < top_sprites[0][0]:
            continue
        for reaction in message.reactions:
            print(reaction.emoji, ":", reaction.count)
            async for user in reaction.users():
                reaction_ids.add(user.id)

        if len(top_sprites) == top_count:
            heapq.heapreplace(top_sprites, (len(reaction_ids), tiebreak_counter, message))
        else:
            heapq.heappush(top_sprites, (len(reaction_ids), tiebreak_counter, message))
        tiebreak_counter += 1
    print([(item[2].content, item[0]) for item in top_sprites])
    output_message = ""
    for i in range(len(top_sprites)):
        line = f"{len(top_sprites) - i}: [{top_sprites[i][2].content}]({top_sprites[i][2].jump_url}) | Unique Reactions: {top_sprites[i][0]}"
        output_message += line + "\n"
    await interaction.followup.send(output_message)


def chunk_array(in_list, n):
    for i in range(0, len(in_list), n):
        yield in_list[i:i + n]

feebas.run(TOKEN)

