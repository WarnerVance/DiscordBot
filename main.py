import discord
from discord.ext import commands
import certifi
import ssl
import functions as fn

# Create a custom SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Set up the bot with command prefix '!' and the SSL context
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def addpledge(ctx, name: str):
    await ctx.send(f"{name} has been added to the pledges list! Exit Code: {fn.add_pledge(name)}")

@bot.command()
async def getpoints(ctx, name: str):
    await ctx.send(f"{name} has {fn.get_pledge_points(name)} points!")
   

@bot.command()
async def updatepoints(ctx, name: str, point_change: int):
    await ctx.send(f"Exit Code: {fn.update_points(name, point_change)}")

@bot.command()
async def getpledges(ctx):
    await ctx.send(f"Pledges: {fn.get_pledges()}")

@bot.command()
async def getgraph(ctx):
    await ctx.send(file=discord.File(fn.get_points_graph()))

@bot.command()
async def getranking(ctx):
    rankings = fn.get_ranked_pledges()
    response = "\n".join(rankings)
    await ctx.send(f"Current Rankings:\n{response}")

@bot.command()
async def deletepledge(ctx, name: str):
    await ctx.send(f"Exit Code: {fn.delete_pledge(name)}")


# Replace 'YOUR_TOKEN_HERE' with your actual Discord bot token
bot.run('MTMxNTEzMTkyMjM1NTE5NTk3NQ.GX3X8s.R5macDjnwGibLgvY0RzUiBP-5uiyOCxHczsmZQ')
