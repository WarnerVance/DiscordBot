# Import required libraries for Discord bot functionality
import os                                  # File and path operations
import discord                            # Discord API wrapper
from discord.ext import commands, tasks   # Discord bot commands and scheduled tasks
from discord import app_commands          # Discord slash commands
import certifi                            # SSL certificate handling
import ssl                                # Secure connection support
import functions as fn                    # Custom functions for pledge management
import asyncio                            # Asynchronous I/O support
import functools                          # Function and decorator tools
from datetime import datetime, time as datetime_time  # Date and time handling
import pytz                               # Timezone support
import logging                            # Logging functionality
import time                               # Time operations

# Define custom logging level for command tracking
COMMAND_LEVEL = 25  # Set between INFO (20) and WARNING (30)
logging.addLevelName(COMMAND_LEVEL, 'COMMAND')

# Add custom command logging method to Logger class
def command(self, message, *args, **kwargs):
    if self.isEnabledFor(COMMAND_LEVEL):
        self._log(COMMAND_LEVEL, message, args, **kwargs)
logging.Logger.command = command

# Configure logging system with both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),   # Log to file
        logging.StreamHandler()           # Log to console
    ]
)
logger = logging.getLogger('discord_bot')

# Initialize SSL context for secure connections
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Set up Discord bot with required permissions
intents = discord.Intents.default()
intents.message_content = True            # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

# Event handler for when bot successfully connects to Discord
@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    try:
        # Synchronize slash commands with Discord's API
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        logger.info(f"Synced commands: {[command.name for command in synced]}")
    except Exception as e:
        logger.error(f"Error syncing commands: {str(e)}")

# Helper function to verify if user has the Brother role
async def check_brother_role(interaction: discord.Interaction) -> bool:
    brother_role = discord.utils.get(interaction.guild.roles, name="Brother")
    if brother_role is None or brother_role not in interaction.user.roles:
        await interaction.response.send_message("You must have the Brother role to use this command.", ephemeral=True)
        return False
    return True

# Decorator function to add timeout functionality to commands
def timeout_command(seconds=10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            try:
                # Execute command with timeout
                async with asyncio.timeout(seconds):
                    await func(interaction, *args, **kwargs)
            except asyncio.TimeoutError:
                # Handle timeout case
                if not interaction.response.is_done():
                    await interaction.response.send_message("Command timed out after 10 seconds.", ephemeral=True)
        return wrapper
    return decorator

# Decorator function for logging command usage
def log_command():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(interaction: discord.Interaction, *args, **kwargs):
            # Extract command information
            command_name = func.__name__
            user = interaction.user.display_name
            guild = interaction.guild.name if interaction.guild else "DM"
            # Log command execution
            logger.command(f"Command '{command_name}' executed by {user} in {guild} with args: {args} kwargs: {kwargs}")
            return await func(interaction, *args, **kwargs)
        return wrapper
    return decorator

# Helper function for pledge name autocomplete in commands
async def pledge_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    # Get list of pledges and filter based on current input
    pledges = fn.get_pledges()
    return [
        app_commands.Choice(name=pledge, value=pledge)
        for pledge in pledges
        if current.lower() in pledge.lower()
    ][:25]  # Discord has a limit of 25 choices

# Convert commands to slash commands
@bot.tree.command(
    name="add_pledge",
    description="Add a new pledge to the list"
)
@log_command()
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

@bot.tree.command(
    name="get_pledge_points",
    description="Get points for a specific pledge"
)
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
async def getpoints(interaction: discord.Interaction, name: str, comment: str = None):
    if not await check_brother_role(interaction):
        return
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    await interaction.response.send_message(f"{caller} checked: {name} has {fn.get_pledge_points(name)} points!{comment_text}")

@bot.tree.command(
    name="change_pledge_points",
    description="Update points for a specific pledge",
    extras={"emoji": "📝"}
)
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
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
        await interaction.response.send_message("Error: Point change cannot exceed 35 points at once!", ephemeral=True)
        return

    # Pass the comment to the update_points function
    result = fn.update_points(name, point_change, comment)
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

@bot.tree.command(
    name="list_pledges",
    description="Get list of all pledges"
)
@log_command()
async def getpledges(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Pledges: {fn.get_pledges()}")

@bot.tree.command(name="show_points_graph", description="Display current points distribution graph")
@timeout_command()
@log_command()
async def getgraph(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_graph()))

@bot.tree.command(name="show_pledge_ranking", description="Display current pledge rankings")
@log_command()
async def getranking(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    rankings = fn.get_ranked_pledges()
    response = "\n".join(rankings)
    await interaction.response.send_message(f"Current Rankings:\n{response}")

@bot.tree.command(name="remove_pledge", description="Remove a pledge from the list")
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
async def deletepledge(interaction: discord.Interaction, name: str):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Exit Code: {fn.delete_pledge(name)}")

@bot.tree.command(name="export_points_file", description="Export the points data as CSV file")
@app_commands.default_permissions()
@log_command()
async def getpointsfile(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_file()))

@bot.tree.command(name="show_points_history", description="Display a graph with points progression over time")
@timeout_command()
@log_command()
async def getpointstime(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_over_time()))

@bot.tree.command(name="log_size", description="Get the current size of the bot's log file")
@app_commands.default_permissions()
@log_command()
async def getlogsize(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
        
    try:
        if not os.path.exists('bot.log'):
            await interaction.response.send_message("Log file does not exist.", ephemeral=True)
            return
            
        size_bytes = os.path.getsize('bot.log')
        
        # Convert to appropriate unit
        if size_bytes < 1024:
            size_str = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_str = f"{size_bytes/1024:.2f} KB"
        else:
            size_str = f"{size_bytes/(1024*1024):.2f} MB"
            
        await interaction.response.send_message(f"Current log file size: {size_str}")
        
    except Exception as e:
        logger.error(f"Error getting log file size: {str(e)}")
        await interaction.response.send_message(f"An error occurred while getting log file size: {str(e)}", ephemeral=True)

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

@bot.tree.command(name="show_logs", description="Get bot logs (defaults to past 24 hours)")
@app_commands.default_permissions()
async def getlogs(interaction: discord.Interaction, hours: int = 24):
    if not await check_brother_role(interaction):
        return
        
    # Validate hours input
    if hours <= 0:
        await interaction.response.send_message("Hours must be a positive number.", ephemeral=True)
        return
    if hours > 168:  # 1 week limit
        await interaction.response.send_message("Cannot retrieve more than 168 hours (1 week) of logs.", ephemeral=True)
        return
        
    recent_logs, error = fn.get_recent_logs(hours)
    if error:
        await interaction.response.send_message(error, ephemeral=True)
        return
            
    with open('recent_logs.txt', 'w') as f:
        f.writelines(recent_logs)
        
    await interaction.response.send_message(
        f"Showing logs from the past {hours} hours (most recent first):",
        file=discord.File('recent_logs.txt')
    )
    
    os.remove('recent_logs.txt')

@bot.tree.command(name="shutdown", description="Safely shutdown the bot (Admin only)")
@app_commands.default_permissions()
@log_command()
async def shutdown(interaction: discord.Interaction):
    if not await check_brother_role(interaction):
        return
        
    try:
        await interaction.response.send_message("🔄 Bot is shutting down...")
        logger.info(f"Bot shutdown initiated by {interaction.user.display_name}")
        
        # Stop the midnight update task if it's running
        if midnight_update.is_running():
            midnight_update.cancel()
            
        # Close the bot connection
        await bot.close()
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        await interaction.response.send_message(f"❌ Error during shutdown: {str(e)}", ephemeral=True)

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

