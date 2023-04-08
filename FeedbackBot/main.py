import discord
from discord import app_commands
from discord.utils import get
import random
import os

# from config import TOKEN, GUILD_ID, ROLE_ID
TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = os.environ["DISCORD_GUILD_ID"]
ROLE_ID = os.environ["DISCORD_ROLE_ID"]

intents = discord.Intents.default()
intents.messages = True
intents.members = True


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
    guild = feebas.get_guild(GUILD_ID)
    role = get(guild.roles, id=ROLE_ID)
    sample_count = 5
    sample = []
    if sample_count <= len(role.members):
        sample = random.sample(role.members, sample_count)
    else:
        sample = role.members
    tags = [f"<@{member.id}>" for member in sample]
    joined_tags = '\n'.join(tags)
    await interaction.response.send_message(f"YOU HAVE BEEN SUMMONED:\n{joined_tags}", ephemeral=False)

feebas.run(TOKEN)

