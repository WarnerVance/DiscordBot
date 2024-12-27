# Import required libraries
import os
import time
from datetime import datetime

import discord
import pandas as pd

from CheckRoles import check_pledge
from PointSystem import logger, get_pledges


# Initialize logger for this module


def add_pledge(name):
    """
    Add a new pledge to the system
    Args:
        name (str): Name of pledge to add
    Returns:
        int: 0 for success, 1 if pledge already exists or invalid
    """
    # Input validation
    if not isinstance(name, str) or not name.strip():
        return 1
    if len(name) > 50:  # Add length validation
        return 1
    
    if check_pledge(name):
        return 1
    else:
        with open('pledges.csv', 'a') as fil:
            fil.write(f"{name}\n")
    return 0


def delete_pledge(name: str):
    """
    Remove a pledge from the system
    Args:
        name (str): Name of pledge to delete
    Returns:
        int: 0 for success, 1 if pledge doesn't exist
    """
    # Read all pledges
    pledges = get_pledges()
    
    # Check if pledge exists
    if name not in pledges:
        return 1
    
    # Remove pledge from list
    pledges.remove(name)
    
    # Write updated list back to file
    with open('pledges.csv', 'w') as fil:
        for pledge in pledges:
            fil.write(f"{pledge}\n")
    # Verify the pledge was actually deleted
    if name in get_pledges():
        logger.error(f"Failed to delete pledge {name}")
        return 1
        
    logger.info(f"Successfully deleted pledge {name}")
    return 0


def get_recent_logs(hours: int = 24) -> tuple[list[str], str]:
    """
    Retrieve logs from the past specified hours
    Args:
        hours (int): Number of hours to look back (default: 24)
    Returns:
        tuple: (list of log lines, error message)
        If error_message is not empty, log_lines will be empty
    """
    try:
        now = time.time()
        past_time = now - (hours * 60 * 60)
        
        # Check if log file exists
        if not os.path.exists('bot.log'):
            return [], "Log file does not exist."
            
        # Read and process log files
        with open('bot.log', 'r') as f:
            logs = f.readlines()
            
        if not logs:
            return [], "Log file is empty."
            
        # Filter logs by time
        recent_logs = []
        for line in logs:
            try:
                timestamp = line.split(' - ')[0].strip()
                log_time = time.mktime(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f').timetuple())
                if log_time >= past_time:
                    recent_logs.append(line)
            except Exception as e:
                logger.error(f"Error processing log line '{line}': {str(e)}")
                continue
                
        if not recent_logs:
            return [], (f"No logs found from the past {hours} hours.\n"
                       f"Current time: {datetime.fromtimestamp(now)}\n"
                       f"Looking for logs after: {datetime.fromtimestamp(past_time)}")
            
        # Sort logs in reverse chronological order
        recent_logs.sort(reverse=True)
        return recent_logs, ""
        
    except Exception as e:
        logger.error(f"Error retrieving logs: {str(e)}")
        return [], f"An error occurred while retrieving logs: {str(e)}"


def clean_old_logs():
    """
    Delete log entries that are more than 3 days old from bot.log
    """
    try:
        if not os.path.exists('bot.log'):
            logger.warning("No log file found to clean")
            return
            
        # Calculate cutoff time (3 days ago)
        now = time.time()
        cutoff_time = now - (3 * 24 * 60 * 60)  # 3 days in seconds
        
        # Read existing logs
        with open('bot.log', 'r') as f:
            logs = f.readlines()
            
        if not logs:
            return
            
        # Filter logs newer than cutoff
        recent_logs = []
        for line in logs:
            try:
                timestamp = line.split(' - ')[0].strip()
                log_time = time.mktime(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f').timetuple())
                if log_time >= cutoff_time:
                    recent_logs.append(line)
            except Exception as e:
                logger.error(f"Error processing log line during cleanup: {str(e)}")
                recent_logs.append(line)  # Keep lines we can't parse to be safe
                
        # Write filtered logs back to file
        with open('bot.log', 'w') as f:
            f.writelines(recent_logs)
            
        logger.info(f"Cleaned {len(logs) - len(recent_logs)} old log entries")
        
    except Exception as e:
        logger.error(f"Error cleaning old logs: {str(e)}")

class PointsPlotView(discord.ui.View):
    def __init__(self, df, pledges):
        super().__init__(timeout=300)  # 5 minute timeout
        self.df = df
        self.pledges = pledges
        self.current_pledge = pledges[0] if pledges else None
        
    @discord.ui.button(label="Previous Pledge", style=discord.ButtonStyle.primary)
    async def prev_pledge(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pledges:
            await interaction.response.send_message("No pledges available", ephemeral=True)
            return
            
        current_idx = self.pledges.index(self.current_pledge)
        self.current_pledge = self.pledges[current_idx - 1]
        await self.update_plot(interaction)

    @discord.ui.button(label="Next Pledge", style=discord.ButtonStyle.primary)
    async def next_pledge(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.pledges:
            await interaction.response.send_message("No pledges available", ephemeral=True)
            return
            
        current_idx = self.pledges.index(self.current_pledge)
        self.current_pledge = self.pledges[(current_idx + 1) % len(self.pledges)]
        await self.update_plot(interaction)

    async def update_plot(self, interaction: discord.Interaction):
        import matplotlib.pyplot as plt
        
        # Filter data for current pledge
        pledge_data = self.df[self.df['Name'] == self.current_pledge].copy()
        pledge_data = pledge_data.sort_values('Time')
        pledge_data['Cumulative'] = pledge_data['Point_Change'].cumsum()
        
        # Create plot
        plt.figure(figsize=(10, 6))
        plt.plot(pledge_data['Time'], pledge_data['Cumulative'], marker='o')
        plt.title(f'Points Over Time - {self.current_pledge}')
        plt.xlabel('Date')
        plt.ylabel('Total Points')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save temporary file
        temp_filename = f'temp_plot_{int(time.time())}.png'
        plt.savefig(temp_filename)
        plt.close()
        
        # Send updated plot
        await interaction.response.edit_message(
            content=f"Showing points for: {self.current_pledge}",
            attachments=[discord.File(temp_filename)],
            view=self
        )
        
        # Clean up temporary file
        os.remove(temp_filename)

async def interactive_plot(interaction: discord.Interaction):
    """
    Create an interactive plot using Discord's native buttons
    
    Args:
        interaction (discord.Interaction): The Discord interaction
    """
    try:
        # Read and prepare data
        import matplotlib.pyplot as plt
        df = pd.read_csv('Points.csv')
        df['Time'] = pd.to_datetime(df['Time'], unit='s')
        
        # Get active pledges
        pledges = get_pledges()
        if not pledges:
            await interaction.response.send_message("No pledges found in the system.")
            return
            
        # Create view with initial plot
        view = PointsPlotView(df, pledges)
        
        # Generate initial plot
        temp_filename = f'temp_plot_{int(time.time())}.png'
        pledge_data = df[df['Name'] == view.current_pledge].copy()
        pledge_data = pledge_data.sort_values('Time')
        pledge_data['Cumulative'] = pledge_data['Point_Change'].cumsum()
        
        plt.figure(figsize=(10, 6))
        plt.plot(pledge_data['Time'], pledge_data['Cumulative'], marker='o')
        plt.title(f'Points Over Time - {view.current_pledge}')
        plt.xlabel('Date')
        plt.ylabel('Total Points')
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(temp_filename)
        plt.close()
        
        # Send initial message with plot
        await interaction.response.send_message(
            content=f"Showing points for: {view.current_pledge}",
            file=discord.File(temp_filename),
            view=view
        )
        
        # Clean up temporary file
        os.remove(temp_filename)
        
    except Exception as e:
        logger.error(f"Error in interactive_plot: {str(e)}")
        await interaction.response.send_message(
            "An error occurred while creating the interactive plot.",
            ephemeral=True
        )
