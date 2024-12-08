import discord
from discord.ext import commands
from discord import app_commands
import certifi
import ssl
import functions as fn
import asyncio
import functools
from datetime import datetime, time
import pytz

# Create a custom SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Set up the bot with the SSL context
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
        print(f"Synced commands: {[command.name for command in synced]}")
    except Exception as e:
        print(f"Error syncing commands: {str(e)}")

# Helper function to check for Brother role
async def check_brother_role(interaction: discord.Interaction) -> bool:
    brother_role = discord.utils.get(interaction.guild.roles, name="Brother")
    if brother_role is None or brother_role not in interaction.user.roles:
        await interaction.response.send_message("You must have the Brother role to use this command.", ephemeral=True)
        return False
    return True

# Add this decorator function
def timeout_command(seconds=10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            try:
                async with asyncio.timeout(seconds):
                    await func(interaction, *args, **kwargs)
            except asyncio.TimeoutError:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Command timed out after 10 seconds.", ephemeral=True)
        return wrapper
    return decorator

# Convert commands to slash commands
@bot.tree.command(name="add_pledge", description="Add a new pledge to the list")
async def addpledge(interaction: discord.Interaction, name: str):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"{name} has been added to the pledges list! Exit Code: {fn.add_pledge(name)}")

@bot.tree.command(name="get_pledge_points", description="Get points for a specific pledge")
async def getpoints(interaction: discord.Interaction, name: str):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"{name} has {fn.get_pledge_points(name)} points!")

@bot.tree.command(name="update_pledge_points", description="Update points for a specific pledge")
async def updatepoints(interaction: discord.Interaction, name: str, point_change: int):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"You gave {name} {point_change} points! Exit Code: {fn.update_points(name, point_change)}")

@bot.tree.command(name="list_pledges", description="Get list of all pledges")
async def getpledges(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Pledges: {fn.get_pledges()}")

@bot.tree.command(name="show_points_graph", description="Display current points distribution graph")
@timeout_command()
async def getgraph(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_graph()))

@bot.tree.command(name="show_pledge_ranking", description="Display current pledge rankings")
async def getranking(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    rankings = fn.get_ranked_pledges()
    response = "\n".join(rankings)
    await interaction.response.send_message(f"Current Rankings:\n{response}")

@bot.tree.command(name="remove_pledge", description="Remove a pledge from the list")
async def deletepledge(interaction: discord.Interaction, name: str):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Exit Code: {fn.delete_pledge(name)}")

@bot.tree.command(name="export_points_file", description="Export the points data as CSV file")
@app_commands.default_permissions()
async def getpointsfile(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_file()))

@bot.tree.command(name="show_points_history", description="Display points progression over time")
@timeout_command()
async def getpointstime(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_over_time()))

@tasks.loop(time=[time(5, 0), time(6, 0)])  # Runs at 00:00 CT (either 05:00 or 06:00 UTC)
async def midnight_update():
    # Find the 'general' channel in all guilds the bot is in
    for guild in bot.guilds:
        general_channel = discord.utils.get(guild.text_channels, name='general')
        if general_channel:
            # Send Points.csv file
            await general_channel.send(file=discord.File('Points.csv'))
            
            # Get and send current pledge rankings
            rankings = fn.get_ranked_pledges()
            await general_channel.send("Current Pledge Rankings:\n" + "\n".join(rankings))

# Replace 'YOUR_TOKEN_HERE' with your actual Discord bot token
bot.run('MTMxNTEzMTkyMjM1NTE5NTk3NQ.GX3X8s.R5macDjnwGibLgvY0RzUiBP-5uiyOCxHczsmZQ')


