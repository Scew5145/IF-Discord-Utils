import discord
from discord import app_commands
from discord.utils import get
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


@tree.command(guild=discord.Object(id=GUILD_ID), description="tag 5 random members with the feedback giver role")
async def feedbackpls(interaction: discord.Interaction):
    guild = interaction.guild
    role = get(guild.roles, id=ROLE_ID)
    sample_count = 9
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
    tags = [f"<@{member.id}>" for member in sample]
    # tags = ["bacon"]
    joined_tags = '\n'.join(tags)
    await interaction.response.send_message(f"THESE PEOPLE HAVE BEEN (forcefully) RECRUITED TO GIVE YOU FEEDBACK:\n{joined_tags}\n (feedbackers can get the Sprite Feedback Giver role removed if they don't want these pings)", ephemeral=False)


def chunk_array(in_list, n):
    for i in range(0, len(in_list), n):
        yield in_list[i:i + n]

feebas.run(TOKEN)

