import discord
from discord.ext import commands, tasks
from discord import app_commands
import certifi
import ssl
import functions as fn
import asyncio
import functools
from datetime import datetime, time as datetime_time
import pytz
import logging
import time

# Add logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('discord_bot')

# Create a custom SSL context
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Set up the bot with the SSL context
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        logger.info(f"Synced commands: {[command.name for command in synced]}")
    except Exception as e:
        logger.error(f"Error syncing commands: {str(e)}")

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
async def addpledge(interaction: discord.Interaction, name: str, comment: str = None):
    if not await check_brother_role(interaction):
        return
    
    # Validate name
    name = name.strip()
    if not name:
        await interaction.response.send_message("Error: Pledge name cannot be empty!", ephemeral=True)
        return
    if len(name) > 50:
        await interaction.response.send_message("Error: Pledge name is too long! Keep it under 50 characters.", ephemeral=True)
        return
    if not name.replace(' ', '').isalnum():
        await interaction.response.send_message("Error: Pledge name can only contain letters, numbers, and spaces!", ephemeral=True)
        return

    result = fn.add_pledge(name)
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    if result == 0:
        await interaction.response.send_message(f"✅ {caller} added {name} to the pledges list!{comment_text}")
    else:
        await interaction.response.send_message(f"❌ {caller} failed to add {name}. They might already be in the list.{comment_text}", ephemeral=True)

@bot.tree.command(name="get_pledge_points", description="Get points for a specific pledge")
async def getpoints(interaction: discord.Interaction, name: str, comment: str = None):
    if not await check_brother_role(interaction):
        return
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    await interaction.response.send_message(f"{caller} checked: {name} has {fn.get_pledge_points(name)} points!{comment_text}")

@bot.tree.command(name="change_pledge_points", description="Update points for a specific pledge")
async def updatepoints(interaction: discord.Interaction, name: str, point_change: int, comment: str = None):
    if not await check_brother_role(interaction):
        return
    
    # Validate inputs
    name = name.strip()
    if not name:
        await interaction.response.send_message("Error: Pledge name cannot be empty!", ephemeral=True)
        return
        
    if point_change == 0:
        await interaction.response.send_message("Warning: Point change is 0. No changes made.", ephemeral=True)
        return
        
    if abs(point_change) > 35:
        await interaction.response.send_message("Error: Point change cannot exceed 100 points at once!", ephemeral=True)
        return

    result = fn.update_points(name, point_change)
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    if result == 0:
        emoji = "🔺" if point_change > 0 else "🔻"
        await interaction.response.send_message(
            f"{emoji} {caller} updated points for {name}:\n"
            f"Change: {point_change:+d} points{comment_text}"
        )
    else:
        await interaction.response.send_message(f"❌ {caller} failed to find pledge named '{name}'{comment_text}", ephemeral=True)

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

# Add error handling for commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"⏳ This command is on cooldown. Please wait {error.retry_after:.1f} seconds.", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.", 
            ephemeral=True
        )
    elif isinstance(error, app_commands.TransformerError):
        await interaction.response.send_message(
            f"❌ Invalid input: {str(error)}\nPlease check your command and try again.", 
            ephemeral=True
        )
    else:
        logger.error(f"Command error: {str(error)}")
        await interaction.response.send_message(
            "❌ Oops! Something went wrong. Please try again later or contact an admin if the problem persists.", 
            ephemeral=True
        )

# Add reconnection logic
@bot.event
async def on_disconnect():
    logger.warning("Bot disconnected from Discord")

@bot.event
async def on_connect():
    logger.info("Bot reconnected to Discord")

# Modify the midnight_update task to include error handling
@tasks.loop(time=[datetime_time(5, 0), datetime_time(6, 0)])
async def midnight_update():
    try:
        for guild in bot.guilds:
            general_channel = discord.utils.get(guild.text_channels, name='general')
            if general_channel:
                try:
                    await general_channel.send(file=discord.File('Points.csv'))
                    rankings = fn.get_ranked_pledges()
                    await general_channel.send("Current Pledge Rankings:\n" + "\n".join(rankings))
                    logger.info(f"Successfully sent midnight update to {guild.name}")
                except Exception as e:
                    logger.error(f"Error sending midnight update to {guild.name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error in midnight_update task: {str(e)}")

@bot.tree.command(name="show_logs", description="Get bot logs from the past 24 hours")
@app_commands.default_permissions()
async def getlogs(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return        
    try:
        # Get current time using proper time module
        now = time.time()
        yesterday = now - (24 * 60 * 60)
        
        # First check if file exists and has content
        import os
        if not os.path.exists('bot.log'):
            await interaction.response.send_message("Log file does not exist.", ephemeral=True)
            return
            
        # Read log file and filter last 24 hours
        with open('bot.log', 'r') as f:
            logs = f.readlines()
            
        if not logs:
            await interaction.response.send_message("Log file is empty.", ephemeral=True)
            return
            
        recent_logs = []
        for line in logs:
            try:
                # Parse timestamp from log line
                timestamp = line.split(' - ')[0].strip()  # Added strip() to remove whitespace
                log_time = time.mktime(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f').timetuple())  # Added milliseconds format
                if log_time >= yesterday:
                    recent_logs.append(line)
                logger.debug(f"Processed log line with timestamp: {timestamp}, log_time: {log_time}, yesterday: {yesterday}")
            except Exception as e:
                logger.error(f"Error processing log line '{line}': {str(e)}")
                continue
                
        if not recent_logs:
            await interaction.response.send_message(
                f"No logs found from the past 24 hours.\n"
                f"Current time: {datetime.fromtimestamp(now)}\n"
                f"Looking for logs after: {datetime.fromtimestamp(yesterday)}",
                ephemeral=True
            )
            return
            
        # Write filtered logs to temporary file
        with open('recent_logs.txt', 'w') as f:
            f.writelines(recent_logs)
            
        # Send file
        await interaction.response.send_message(file=discord.File('recent_logs.txt'))
        
        # Clean up temp file
        os.remove('recent_logs.txt')
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        await interaction.response.send_message(f"An error occurred while retrieving logs: {str(e)}", ephemeral=True)


# Start the midnight_update task when the bot is ready
@midnight_update.before_loop
async def before_midnight_update():
    await bot.wait_until_ready()


# Modify the bot startup to properly initialize the client
async def main():
    try:
        # First set up the bot
        await bot.login('MTMxNTEzMTkyMjM1NTE5NTk3NQ.GX3X8s.R5macDjnwGibLgvY0RzUiBP-5uiyOCxHczsmZQ')
        
        # Start the midnight update task
        midnight_update.start()
        
        # Then connect and start processing events
        await bot.connect()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
    finally:
        if not bot.is_closed():
            await bot.close()



# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {str(e)}")


