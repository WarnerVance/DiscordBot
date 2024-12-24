# Import required libraries for Discord bot functionality
import asyncio  # Asynchronous I/O support
import functools  # Function and decorator tools
import os  # File and path operations
import platform  # System information
import ssl  # Secure connection support
import time
from datetime import datetime, time as datetime_time  # Date and time handling

import certifi  # SSL certificate handling
import discord  # Discord API wrapper
import pandas as pd
import psutil  # System information
import pytz  # Timezone support
from discord import app_commands  # Discord slash commands
from discord.ext import commands, tasks  # Discord bot commands and scheduled tasks
from dotenv import load_dotenv

import functions as fn  # Custom functions for pledge management
import interviews as interviews
from logging_config import setup_logging  # Add this import

# Get configured logger
logger = setup_logging()

# Initialize SSL context for secure connections
ssl_context = ssl.create_default_context(cafile=certifi.where())

# Set up Discord bot with required permissions
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)
bot.start_time = None

load_dotenv()  # Load environment variables from .env file
TOKEN = os.getenv('DISCORD_TOKEN')


# Event handler for when bot successfully connects to Discord
@bot.event
async def on_ready():
    if bot.start_time is None:  # Only set on first connection
        bot.start_time = datetime.now(pytz.UTC)

    # Initialize required CSV files if they don't exist
    try:
        # Create pledges.csv if it doesn't exist
        if not os.path.exists('pledges.csv'):
            logger.info("Creating pledges.csv file")
            with open('pledges.csv', 'w') as f:
                f.write("")  # Create empty file

        # Create Points.csv if it doesn't exist
        if not os.path.exists('Points.csv'):
            logger.info("Creating Points.csv file")
            df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
            df.to_csv("Points.csv", index=False)
            del df

        # Create PendingPoints.csv if it doesn't exist
        if not os.path.exists('PendingPoints.csv'):
            logger.info("Creating PendingPoints.csv file")
            df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments", "Requester"])
            df.to_csv("PendingPoints.csv", index=False)
            del df
        # Create interviews.csv if it doesn't exist
        if not os.path.exists('interviews.csv'):
            logger.info("Creating PendingPoints.csv file")
            df = pd.DataFrame(columns=["Time", "Pledge", "Brother", "Quality"])
            df.to_csv("interviews.csv", index=False)
            del df


    except Exception as e:
        logger.error(f"Error initializing CSV files: {str(e)}")

    logger.info(f'{bot.user} has connected to Discord!')
    try:
        # Synchronize slash commands with Discord's API
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        logger.info(f"Synced commands: {[command.name for command in synced]}")
    except Exception as e:
        logger.error(f"Error syncing commands: {str(e)}")


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
    try:
        # Get list of pledges and filter based on current input
        pledges = fn.get_pledges()
        choices = [
            app_commands.Choice(name=pledge, value=pledge)
            for pledge in pledges
            if current.lower() in pledge.lower()
        ]
        # Discord has a limit of 25 choices
        return choices[:25]
    except Exception as e:
        logger.error(f"Error in pledge_name_autocomplete: {str(e)}")
        # Return empty list on error to prevent command failure
        return []


# Convert commands to slash commands
@bot.tree.command(
    name="add_pledge",
    description="Add a new pledge to the list"
)
@log_command()
async def addpledge(interaction: discord.Interaction, name: str, comment: str = None):
    if not await fn.check_brother_role(interaction):
        return

    # Validate name
    name = name.strip()
    if not name:
        await interaction.response.send_message("Error: Pledge name cannot be empty!", ephemeral=True)
        return
    if len(name) > 50:
        await interaction.response.send_message("Error: Pledge name is too long! Keep it under 50 characters.",
                                                ephemeral=True)
        return
    if not name.replace(' ', '').isalnum():
        await interaction.response.send_message("Error: Pledge name can only contain letters, numbers, and spaces!",
                                                ephemeral=True)
        return

    result = fn.add_pledge(name)
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    if result == 0:
        await interaction.response.send_message(f"✅ {caller} added {name} to the pledges list!{comment_text}")
    else:
        await interaction.response.send_message(
            f"❌ {caller} failed to add {name}. They might already be in the list.{comment_text}", ephemeral=True)


@bot.tree.command(
    name="get_pledge_points",
    description="Get points for a specific pledge"
)
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
async def getpoints(interaction: discord.Interaction, name: str, comment: str = None):
    if not await fn.check_brother_role(interaction):
        return
    comment_text = f"\nComment: {comment}" if comment else ""
    caller = interaction.user.display_name
    await interaction.response.send_message(
        f"{caller} checked: {name} has {fn.get_pledge_points(name)} points!{comment_text}")


@bot.tree.command(
    name="change_pledge_points",
    description="Request a points change for a pledge",
    extras={"emoji": "📝"}
)
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
async def updatepoints(interaction: discord.Interaction, name: str, point_change: int, comment: str):
    if not await fn.check_brother_role(interaction):
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

    if not comment or not comment.strip():
        await interaction.response.send_message("Error: A comment is required when changing points!", ephemeral=True)
        return

    # Use add_pending_points instead of direct update
    result = fn.add_pending_points(name, point_change, comment, interaction.user.display_name)
    if result == 0:
        emoji = "🔺" if point_change > 0 else "🔻"
        await interaction.response.send_message(
            f"{emoji} Points change requested by {interaction.user.display_name}:\n"
            f"Pledge: {name}\n"
            f"Change: {point_change:+d} points\n"
            f"Comment: {comment}\n"
            f"Status: Awaiting VP Internal approval"
        )
    else:
        await interaction.response.send_message(
            f"❌ Failed to submit points change request for '{name}'",
            ephemeral=True
        )


@bot.tree.command(
    name="list_pledges",
    description="Get list of all pledges"
)
@log_command()
async def getpledges(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Pledges: {fn.get_pledges()}")


@bot.tree.command(name="show_points_graph", description="Display current points distribution graph")
@timeout_command()
@log_command()
async def getgraph(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_graph()))


@bot.tree.command(name="show_pledge_ranking", description="Display current pledge rankings")
@log_command()
async def getranking(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return
    rankings = fn.get_ranked_pledges()
    response = "\n".join(rankings)
    await interaction.response.send_message(f"Current Rankings:\n{response}")


@bot.tree.command(name="remove_pledge", description="Remove a pledge from the list")
@app_commands.autocomplete(name=pledge_name_autocomplete)
@log_command()
async def deletepledge(interaction: discord.Interaction, name: str):
    if not await fn.check_brother_role(interaction):
        return
    await interaction.response.send_message(f"Exit Code: {fn.delete_pledge(name)}")


@bot.tree.command(name="export_points_file", description="Export the points data as CSV file")
@app_commands.default_permissions()
@log_command()
async def getpointsfile(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_file()))


@bot.tree.command(name="show_points_history", description="Display a graph with points progression over time")
@timeout_command()
@log_command()
async def getpointstime(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return
    await interaction.response.send_message(file=discord.File(fn.get_points_over_time()))


@bot.tree.command(name="log_size", description="Get the current size of the bot's log file")
@app_commands.default_permissions()
@log_command()
async def getlogsize(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
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
            size_str = f"{size_bytes / 1024:.2f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"

        await interaction.response.send_message(f"Current log file size: {size_str}")

    except Exception as e:
        logger.error(f"Error getting log file size: {str(e)}")
        await interaction.response.send_message(f"An error occurred while getting log file size: {str(e)}",
                                                ephemeral=True)


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


# Interview Commands

@bot.tree.command(name="add_interview", description="Add a new interview. Quality is binary 1 or 0")
@app_commands.autocomplete(pledge=pledge_name_autocomplete)
@log_command()
async def addinterview(interaction: discord.Interaction, pledge: str, brother: str, quality: int):
    if not await fn.check_brother_role(interaction):
        logger.warning(f"Brother {interaction} authentication failed")
        await interaction.response.send_message("Brother authentication failed.", ephemeral=True)
        return
    if not fn.check_pledge(pledge):
        await interaction.response.send_message("Invalid pledge.")
        logger.error(f"Invalid pledge: {pledge}")
        return
    if quality not in [0, 1]:
        await interaction.response.send_message("Invalid quality. Quality must be 0 or 1.", ephemeral=True)
        logger.error(f"Invalid quality: {quality}")
        return
    await interaction.response.send_message(
        f"Added interview! Exit Code: {interviews.add_interview(pledge, brother, int(quality), time.time())}")


# TODO: Fix this
@bot.tree.command(name="get_interview_rankings", description="Get a list of pledges by number of interviews")
@timeout_command()
@log_command()
async def getinterviewrankings(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        logger.warning(f"Brother {interaction} authentication failed")
        await interaction.response.send_message("Brother authentication failed.", ephemeral=True)
        return
    rankings = interviews.interview_rankings()
    Pledges = pd.Series(rankings).index.tolist()
    Numbers = pd.Series(rankings).values.tolist()
    print(Pledges, Numbers)
    # for i in Pledges:
    #     # fasfd
    #     break
    await interaction.response.send_message("Current Rankings")

# @bot.tree.command(name="interview_summary", description="Get a summary of all interview data")
# @timeout_command()
# @log_command()
# async def getinterviewsummary(interaction: discord.Interaction):
#     if not await fn.check_brother_role(interaction):
#         logger.warning(f"Brother {interaction} authentication failed")
#         await interaction.response.send_message("Brother authentication failed.", ephemeral=True)
#     pledges = fn.get_pledges()
#     n = 0
#     responses = []
#     df = interviews.interview_summary()
#     for i in len(pledges):
#         pledge = pledges[i]
#         responses.append(f"{n}. {pledge}")
#

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
        # Clean old logs first
        logger.info("Starting daily log cleanup")
        fn.clean_old_logs()

        # Send updates to guilds
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
    if not await fn.check_brother_role(interaction):
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


@bot.tree.command(name="shutdown",
                  description="Safely shutdown the bot (Admin only). This will require restarting via ssh or direct access")
@app_commands.default_permissions()
@log_command()
async def shutdown(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
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
        await bot.login(TOKEN)

        # Start the midnight update task
        midnight_update.start()

        # Then connect and start processing events
        await bot.connect()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
    finally:
        if not bot.is_closed():
            await bot.close()


@bot.tree.command(name="status", description="Get bot and server status information")
@app_commands.default_permissions()
@log_command()
async def status(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return

    try:
        # Get bot uptime
        uptime = datetime.now(pytz.UTC) - bot.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds

        # Get server info
        server = interaction.guild
        member_count = server.member_count
        channel_count = len(server.channels)

        # Get bot latency
        latency = round(bot.latency * 1000)  # Convert to milliseconds

        # Get system information
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_used = f"{memory.percent}%"
        disk = psutil.disk_usage('/')
        disk_used = f"{disk.percent}%"

        # Build status message
        status_msg = (
            "🤖 **Bot Status**\n"
            f"Bot Uptime: {uptime_str}\n"
            f"Latency: {latency}ms\n\n"
            "🖥️ **Server Status**\n"
            f"Server Name: {server.name}\n"
            f"Total Members: {member_count}\n"
            f"Total Channels: {channel_count}\n"
            f"Server Created: {server.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            "💻 **Host System**\n"
            f"OS: {platform.system()} {platform.release()}\n"
            f"CPU Usage: {cpu_percent}%\n"
            f"Memory Usage: {memory_used}\n"
            f"Disk Usage: {disk_used}"
        )

        await interaction.response.send_message(status_msg)

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        await interaction.response.send_message(
            "❌ An error occurred while getting status information",
            ephemeral=True
        )


@bot.tree.command(name="interactive_plot", description="Show an interactive plot of pledge points over time")
@log_command()
async def plot(interaction: discord.Interaction):
    """
    Command to display an interactive plot showing pledge points over time
    """
    try:
        if not await fn.check_brother_role(interaction):
            return

        # Check if required files exist
        if not os.path.exists('Points.csv'):
            await interaction.response.send_message("Error: Points.csv file not found.", ephemeral=True)
            return

        # Verify we have pledges
        pledges = fn.get_pledges()
        if not pledges:
            await interaction.response.send_message("No pledges found in the system.", ephemeral=True)
            return

        await fn.interactive_plot(interaction)

    except Exception as e:
        logger.error(f"Error in plot command: {str(e)}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"An error occurred while creating the interactive plot: {str(e)}",
                ephemeral=True
            )


@bot.tree.command(
    name="list_pending_points",
    description="List all pending points changes"
)
@log_command()
async def listpending(interaction: discord.Interaction):
    if not await fn.check_brother_role(interaction):
        return

    df = fn.get_pending_points_csv()
    if df.empty:
        await interaction.response.send_message("No pending points changes.", ephemeral=True)
        return

    # Format pending changes
    pending_list = []
    df = df.reset_index(drop=True)  # Reset index to ensure it starts from 0
    for idx in range(len(df)):
        row = df.iloc[idx]
        emoji = "🔺" if row['Point_Change'] > 0 else "🔻"
        # Add debug print
        logger.info(f"Current index: {idx}")
        pending_list.append(
            f"Index {idx}: {emoji} {row['Name']}: {row['Point_Change']:+d} points\n"  # Changed format here
            f"   Requested by: {row['Requester']}\n"
            f"   Comment: {row['Comments']}"
        )

    await interaction.response.send_message(
        "Pending Points Changes (Resend this command after approval/disapproval becuase indices will change):\n\n" + "\n\n".join(
            pending_list)
    )


@bot.tree.command(
    name="approve_points",
    description="Approve pending points changes (VP Internal only). Use comma-separated indices (e.g., '0,1,3')"
)
@log_command()
async def approvepoints(interaction: discord.Interaction, indices: str):
    if not await fn.check_vp_internal_role(interaction):
        return

    # Parse indices
    try:
        index_list = [int(idx.strip()) for idx in indices.split(',')]
        # Sort in reverse order to handle higher indices first
        index_list.sort(reverse=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid format. Please use comma-separated numbers (e.g., '0,1,3')",
                                                ephemeral=True)
        return

    responses = []
    for index in index_list:
        success, message, point_data = fn.approve_pending_points(index)
        if success:
            emoji = "🔺" if point_data['Point_Change'] > 0 else "🔻"
            responses.append(
                f"✅ Approved points change #{index}:\n"
                f"{emoji} {point_data['Name']}: {point_data['Point_Change']:+d} points\n"
                f"Requested by: {point_data['Requester']}\n"
                f"Comment: {point_data['Comments']}"
            )
        else:
            responses.append(f"❌ Change #{index}: {message}")

    # Reverse the responses so they appear in original index order
    responses.reverse()
    await interaction.response.send_message("\n\n".join(responses))


@bot.tree.command(
    name="reject_points",
    description="Reject pending points changes (VP Internal only). Use comma-separated indices (e.g., '0,1,3')"
)
@log_command()
async def rejectpoints(interaction: discord.Interaction, indices: str):
    if not await fn.check_vp_internal_role(interaction):
        return

    # Parse indices
    try:
        index_list = [int(idx.strip()) for idx in indices.split(',')]
        # Sort in reverse order to handle higher indices first
        index_list.sort(reverse=True)
    except ValueError:
        await interaction.response.send_message("❌ Invalid format. Please use comma-separated numbers (e.g., '0,1,3')",
                                                ephemeral=True)
        return

    responses = []
    for index in index_list:
        success, message, point_data = fn.reject_pending_points(index)
        if success:
            emoji = "🔺" if point_data['Point_Change'] > 0 else "🔻"
            responses.append(
                f"❌ Rejected points change #{index}:\n"
                f"{emoji} {point_data['Name']}: {point_data['Point_Change']:+d} points\n"
                f"Requested by: {point_data['Requester']}\n"
                f"Comment: {point_data['Comments']}"
            )
        else:
            responses.append(f"❌ Change #{index}: {message}")

    # Reverse the responses so they appear in original index order
    responses.reverse()
    await interaction.response.send_message("\n\n".join(responses))


# Run the bot
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {str(e)}")
