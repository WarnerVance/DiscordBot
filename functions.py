# Import required libraries
import os
import time
from datetime import datetime

import discord
import pandas as pd

from logging_config import setup_logging

# Initialize logger for this module
logger = setup_logging()

def check_pledge(name):
    """
    Check if a pledge exists in the pledges.csv file
    Args:
        name (str): Name of pledge to check
    Returns:
        bool: True if pledge exists, False otherwise
    """
    with open('pledges.csv', 'r') as fil:
        pledge_names = [line.rstrip('\n') for line in fil]
        if name in pledge_names:
            return True
        else:
            return False

def get_points_csv():
    """
    Get or create the Points.csv file and return it as a DataFrame
    Returns:
        A pandas DataFrame
    """
    try:
        if not os.path.exists("Points.csv"):
            df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
            df.to_csv("Points.csv", index=False)
        else:
            try:
                df = pd.read_csv("Points.csv")
                # Verify required columns exist
                required_columns = ["Time", "Name", "Point_Change", "Comments"]
                if not all(col in df.columns for col in required_columns):
                    df = pd.DataFrame(columns=required_columns)
            except:
                df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
    except Exception as e:
        logger.error(f"Error in get_points_csv: {str(e)}")
        return pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
    return df

def update_points(name: str, point_change: int, comment: str):
    """
    Update points for a pledge with comprehensive error handling and validation.
    
    Args:
        name (str): The name of the pledge
        point_change (int): The number of points to add/subtract
        comment (str): A required comment about the point change
        
    Returns:
        int: 0 for success, 1 for failure
    """
    try:
        # Input validation
        if not isinstance(name, str) or not name.strip():
            logger.error("Invalid name provided: empty or wrong type")
            return 1
            
        if not isinstance(point_change, (int, float)):
            logger.error(f"Invalid point_change type: {type(point_change)}")
            return 1
            
        # Convert to int and validate range
        point_change = int(point_change)
        if abs(point_change) > 35:  # Enforce point limit
            return 1
            
        if not comment or not isinstance(comment, str) or not comment.strip():
            logger.error("Comment is required and cannot be empty")
            return 1
            
        # Sanitize inputs
        name = name.strip()
        point_change = int(point_change)  # Convert float to int if necessary
        comment = comment.strip()
        
        # Validate and sanitize comment
        if comment is not None:
            if not isinstance(comment, str):
                logger.warning(f"Invalid comment type: {type(comment)}, converting to string")
                comment = str(comment)
            comment = comment.strip()
            # Remove any non-printable characters
            comment = ''.join(c for c in comment if c.isprintable())
            # Truncate very long comments
            if len(comment) > 500:
                logger.warning(f"Comment too long ({len(comment)} chars), truncating")
                comment = comment[:497] + "..."
        
        # Check if pledge exists
        if not check_pledge(name):
            logger.warning(f"Attempted to update points for non-existent pledge: {name}")
            return 1
            
        # Get current points data
        try:
            df = get_points_csv()
        except Exception as e:
            logger.error(f"Failed to read points CSV: {str(e)}")
            return 1
            
        # Prepare new row with validation
        try:
            current_time = time.time()
            new_row = {
                "Time": current_time,
                "Name": name,
                "Point_Change": point_change,
                "Comments": comment if comment else ""
            }
            
            # Validate the new row
            if not pd.isna(new_row["Time"]) and not pd.isna(new_row["Point_Change"]):
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            else:
                logger.error("Invalid data in new row")
                return 1
                
        except Exception as e:
            logger.error(f"Error creating new row: {str(e)}")
            return 1
            
        # Save to CSV with error handling and backup
        try:
            # Create backup of current file
            if os.path.exists("Points.csv"):
                # Create backups directory if it doesn't exist
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                
                # Get list of existing backups sorted by creation time
                existing_backups = []
                if os.path.exists(backup_dir):
                    backup_files = [f for f in os.listdir(backup_dir) if f.startswith("Points_backup_")]
                    existing_backups = sorted(backup_files, reverse=True)
                
                # Remove oldest backups if more than 20 exist
                while len(existing_backups) >= 20:
                    oldest_backup = os.path.join(backup_dir, existing_backups.pop())
                    try:
                        os.remove(oldest_backup)
                    except Exception as e:
                        logger.warning(f"Failed to remove old backup {oldest_backup}: {str(e)}")
                
                # Create new backup
                backup_name = os.path.join(backup_dir, f"Points_backup_{int(current_time)}.csv")
                try:
                    import shutil
                    shutil.copy2("Points.csv", backup_name)
                except Exception as e:
                    logger.warning(f"Failed to create backup: {str(e)}")
            
            # Save new data
            df.to_csv("Points.csv", index=False)
            
            # Verify the save was successful
            if not os.path.exists("Points.csv"):
                logger.error("Failed to save points CSV")
                return 1
                
            # Log successful update
            logger.info(f"Successfully updated points for {name}: {point_change:+d} points")
            return 0
            
        except Exception as e:
            logger.error(f"Failed to save points CSV: {str(e)}")
            # Try to restore from backup if save failed
            if os.path.exists(backup_name):
                try:
                    shutil.copy2(backup_name, "Points.csv")
                    logger.info("Restored from backup after failed save")
                except Exception as backup_e:
                    logger.error(f"Failed to restore from backup: {str(backup_e)}")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error in update_points: {str(e)}")
        return 1

def get_pledge_points(name, df=None):
    """
    Get total points for a specific pledge
    Args:
        name (str): Name of pledge, df (pd.DataFrame): DataFrame of points data (optional, if not given will call get_points_csv)
    Returns:
        int: Total points for pledge, or None if pledge doesn't exist
    """
    if check_pledge(name):
        if df is None:
            df = get_points_csv()
            points = df[df["Name"] == name]["Point_Change"].sum()
            return points
        elif df is not None:
            points = df[df["Name"] == name]["Point_Change"].sum()
            return points
    return None

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

def get_pledges():
    """
    Get list of all pledges
    Returns:
        list: List of pledge names
    """
    with open('pledges.csv', 'r') as fil:
        return [line.rstrip('\n') for line in fil]

def get_points_graph():
    """
    Generate a bar graph of pledge points
    Returns:
        str: Filename of generated graph
    """
    import matplotlib.pyplot as plt
    
    # Get points for each pledge
    pledges = get_pledges()
    points = []
    for pledge in pledges:
        points.append(get_pledge_points(pledge))
    
    # Create bar graph
    plt.figure(figsize=(10,5))
    plt.bar(pledges, points)
    plt.title('Pledge Points')
    plt.xlabel('Pledges')
    plt.ylabel('Points')
    
    # Save and return filename
    filename = 'pledge_points_graph.png'
    plt.savefig(filename)
    plt.close()
    return filename

def get_ranked_pledges():
    """
    Get a sorted list of pledges by their points, including their most recent comment
    Returns:
        list: List of formatted strings with rankings, points, and comments
    """
    try:
        # Validate that required files exist
        if not os.path.exists('pledges.csv'):
            logger.error("pledges.csv file not found")
            return ["Error: Pledge file not found"]
            
        if not os.path.exists('Points.csv'):
            logger.error("Points.csv file not found")
            return ["Error: Points file not found"]
            
        # Get all pledges and their points
        try:
            pledges = get_pledges()
            if not pledges:
                logger.warning("No pledges found in system")
                return ["No pledges currently in system"]
        except Exception as e:
            logger.error(f"Error reading pledges: {str(e)}")
            return ["Error reading pledge data"]
            
        # Initialize list to store pledge data
        pledge_points = []
        try:
            df = get_points_csv()
            if df.empty:
                logger.info("Points file is empty")
                # Still continue, as pledges might just have 0 points
        except Exception as e:
            logger.error(f"Error reading points CSV: {str(e)}")
            return ["Error reading points data"]
        
        # Process each pledge's points and comments
        for pledge in pledges:
            try:
                points = get_pledge_points(pledge)
                if points is None:  # Extra validation
                    points = 0
                    logger.warning(f"No points found for {pledge}, defaulting to 0")
                
                # Get the most recent comment with additional validation
                recent_comment = ""
                pledge_df = df[df["Name"] == pledge]
                
                if not pledge_df.empty:
                    try:
                        last_comment = pledge_df.iloc[-1]["Comments"]
                        # Comprehensive comment validation
                        if pd.notna(last_comment):
                            # Convert to string and sanitize
                            comment_str = str(last_comment).strip()
                            # Remove any problematic characters
                            comment_str = ''.join(c for c in comment_str if c.isprintable())
                            if comment_str:  # Only use non-empty comments
                                recent_comment = comment_str
                    except Exception as e:
                        logger.warning(f"Error processing comment for {pledge}: {str(e)}")
                        # Continue without comment rather than failing
                
                pledge_points.append((pledge, points, recent_comment))
                
            except Exception as e:
                logger.error(f"Error processing pledge {pledge}: {str(e)}")
                # Skip this pledge but continue with others
                continue
        
        # Format and return the rankings
        if not pledge_points:
            return ["No valid pledge data found"]
            
        # Sort by points (descending) and name (ascending)
        try:
            ranked_pledges = sorted(pledge_points, key=lambda x: (x[1], x[0].lower()), reverse=True)
        except Exception as e:
            logger.error(f"Error sorting pledges: {str(e)}")
            return ["Error sorting pledge rankings"]
        
        # Format rankings into strings
        formatted_rankings = []
        try:
            for i, (pledge, points, comment) in enumerate(ranked_pledges, 1):
                # Truncate very long comments
                if comment and len(comment) > 100:
                    comment = comment[:97] + "..."
                
                comment_text = f" ({comment})" if comment else ""
                ranking = f"{i}. {pledge}: {points} points{comment_text}"
                
                # Protect against extremely long lines
                if len(ranking) > 1000:
                    ranking = ranking[:997] + "..."
                    
                formatted_rankings.append(ranking)
        except Exception as e:
            logger.error(f"Error formatting rankings: {str(e)}")
            return ["Error formatting rankings"]
            
        return formatted_rankings
        
    except Exception as e:
        logger.error(f"Unexpected error in get_ranked_pledges: {str(e)}")
        return ["An unexpected error occurred while retrieving rankings"]

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

def get_points_file():
    """
    Get the name of the points file
    Returns:
        str: Name of the points file
    """
    return 'Points.csv'

def get_points_over_time():
    """
    Generate a line graph showing how pledge points change over time
    Returns:
        str: Filename of generated graph
    """
    import matplotlib.pyplot as plt
    # Read points data and convert to pandas DataFrame
    df = pd.read_csv('Points.csv')
    
    # Get list of active pledges
    active_pledges = get_pledges()
    
    # Filter DataFrame to only include active pledges
    df = df[df['Name'].isin(active_pledges)]
    
    # Convert timestamp to datetime
    df['Time'] = pd.to_datetime(df['Time'], unit='s')
    
    # Sort by time
    df = df.sort_values('Time')
    
    # Calculate cumulative sums for all pledges at once using groupby
    cumulative_points = df.pivot_table(
        index='Time', 
        columns='Name', 
        values='Point_Change',
        aggfunc='sum'
    ).fillna(0).cumsum()
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    for pledge in cumulative_points.columns:
        plt.plot(
            cumulative_points.index, 
            cumulative_points[pledge], 
            label=pledge, 
            marker='o'
        )
    
    plt.title('Pledge Points Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Points')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save and return filename
    filename = 'points_over_time.png'
    plt.savefig(filename)
    plt.close()
    return filename

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

async def check_brother_role(interaction: discord.Interaction) -> bool:
    """
    Verify if a user has the Brother role.
    
    Args:
        interaction (discord.Interaction): The interaction to check
        
    Returns:
        bool: True if user has Brother role, False otherwise
    """
    brother_role = discord.utils.get(interaction.guild.roles, name="Brother")
    if brother_role is None or brother_role not in interaction.user.roles:
        await interaction.response.send_message("You must have the Brother role to use this command.", ephemeral=True)
        return False
    return True

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

def get_pending_points_csv():
    """
    Get or create the PendingPoints.csv file and return it as a DataFrame
    Returns:
        pd.DataFrame: DataFrame containing pending points data
    """
    try:
        if not os.path.exists("PendingPoints.csv"):
            # Create new DataFrame with all required columns
            df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments", "Requester"])
            df.to_csv("PendingPoints.csv", index=False)
        else:
            df = pd.read_csv("PendingPoints.csv")
    except Exception as e:
        logger.error(f"Error in get_pending_points_csv: {str(e)}")
        return pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments", "Requester"])
    return df

def add_pending_points(name: str, point_change: int, comment: str, requester: str):
    """
    Add a pending points change that requires VP Internal approval
    """
    try:
        if not check_pledge(name):
            return 1
            
        df = get_pending_points_csv()
        
        new_row = {
            "Time": time.time(),
            "Name": name,
            "Point_Change": point_change,
            "Comments": comment,
            "Requester": requester
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv("PendingPoints.csv", index=False)
        return 0
    except Exception as e:
        logger.error(f"Error adding pending points: {str(e)}")
        return 1

async def check_vp_internal_role(interaction: discord.Interaction) -> bool:
    """
    Verify if a user has the VP Internal role.
    """
    vp_role = discord.utils.get(interaction.guild.roles, name="VP Internal")
    if vp_role is None or vp_role not in interaction.user.roles:
        await interaction.response.send_message(
            "You must have the VP Internal role to use this command.", 
            ephemeral=True
        )
        return False
    return True

def approve_pending_points(index: int) -> tuple[bool, str, dict]:
    """
    Approve a pending points change and apply it
    Returns:
        tuple: (success, message, point_data)
    """
    try:
        # Get pending points DataFrame
        df_pending = get_pending_points_csv()
        
        # Validate index
        if index < 0 or index >= len(df_pending):
            return False, f"Invalid index: {index}. Valid range is 0-{len(df_pending)-1}", {}
            
        # Get the point data at the specified index
        point_data = df_pending.iloc[index].to_dict()
        
        # Apply the points change
        result = update_points(
            point_data['Name'],
            point_data['Point_Change'],
            point_data['Comments']
        )
        
        if result == 0:
            # Remove the approved entry
            df_pending = df_pending.drop(index)
            df_pending.to_csv("PendingPoints.csv", index=False)
            return True, "Points approved and applied", point_data
            
        return False, "Failed to apply points", point_data
        
    except Exception as e:
        logger.error(f"Error approving points: {str(e)}")
        return False, f"Error: {str(e)}", {}

def reject_pending_points(index: int) -> tuple[bool, str, dict]:
    """
    Reject and remove a pending points change
    """
    try:
        df_pending = get_pending_points_csv()
        
        # Validate index
        if index < 0 or index >= len(df_pending):
            return False, f"Invalid index: {index}. Valid range is 0-{len(df_pending)-1}", {}
            
        point_data = df_pending.iloc[index].to_dict()
        df_pending = df_pending.drop(index)
        df_pending.to_csv("PendingPoints.csv", index=False)
        return True, "Points rejected", point_data
        
    except Exception as e:
        logger.error(f"Error rejecting points: {str(e)}")
        return False, f"Error: {str(e)}", {}


def add_interview(pledge, brother, quality, time):
    """
    Add a new interview to the database.
    :param pledge: Name of Pledge
    :param brother: Name of brother
    :param quality: int, 0 or 1, 1 for good quality
    :param time: current time.time timestamp
    :return: 0 for success, 1 for failure
    """
    if pledge == '' or brother == '' or time == '':
        logger.error('empty field')
        return 1
    if not check_pledge(pledge):
        logger.error('pledge does not exist')
        return 1
    try:
        df = pd.read_csv('interviews.csv')
    except Exception as e:
        logger.error(f'error reading interviews.csv {e}')
        return 1
    try:
        if quality not in [0, 1]:
            logger.error('Invalid quality')
            return 1
        added_interview = [time, pledge, brother, quality]
        df.loc[len(df)] = added_interview
        df.to_csv('interviews.csv', index=False)
        return 0
    except Exception as e:
        logger.error(f'Error adding interview {e}')
        return 1


def get_pledge_interviews(pledge):
    """
    Gets a dataframe of pledge interviews for a specific pledge
    :param pledge: Name of Pledge to check
    :return: pandas dataframe of pledge interviews. Columns Time,Pledge,Brother,Quality
    """
    try:
        if check_pledge(pledge):
            df = pd.read_csv('interviews.csv')
            return df.loc[df['Pledge'] == pledge]
        else:
            return 1
    except Exception as e:
        logger.error(f'error getting pledge {e}')
        return 1


def get_brother_interviews(brother):
    try:
        df = pd.read_csv('interviews.csv')
        return df.loc[df['Brother'] == brother]
    except Exception as e:
        logger.error(f'error getting brother {e}')


def interview_rankings(df=None):
    """
    Returns a dataframe of interview rankings
    :param df: Optional dataframe of interview rankings. Will read interviews.csv if none provided
    :return: pandas dataframe of interview rankings
    """
    if df is None:
        try:
            df = pd.read_csv('interviews.csv')
        except Exception as e:
            logger.error(f'error reading interviews.csv {e}')
            return 1
    df = df.drop(["Brother", "Quality", "Time"], axis=1)
    grouped = df.groupby('Pledge')
    counts = grouped.value_counts()
    counts = counts.sort_values(ascending=False)
    return counts


def get_quality_interviews(pledge, interview_df=None):
    """
    Get the number of quality interviews for a specific pledge
    :param pledge: Name of Pledge to check
    :param interview_df: Optional: Pledge interview dataframe
    :return: np.int(64)
    """
    if check_pledge(pledge):
        if interview_df is None:
            interview_df = pd.read_csv('interviews.csv')
            interviews = interview_df[interview_df["Pledge"] == pledge]["Quality"].sum()
            interviews = int(interviews)
            return interviews
        elif interview_df is not None:
            interviews = interview_df[interview_df["Pledge"] == pledge]["Quality"].sum()
            interviews = int(interviews)
            return interviews
    return None


def interview_summary(df=None):
    """
    Returns summary of interview
    :param df: Optional input pandas dataframe of interview data
    :return: Pandas Dataframe of summary data with columns 'Pledge', 'NumberOfInterviews', 'PercentQuality', 'NQuality'
    """
    # Load data
    if df is None:
        try:
            df_input = pd.read_csv('interviews.csv')
        except Exception as e:
            logger.error(f'error reading interviews.csv: {e}')
            return 1
    else:
        df_input = df
    df_output = pd.DataFrame(columns=["Pledge", "NumberOfInterviews", "PercentQuality"])
    # Get Pledge Names
    with open('pledges.csv', 'r') as fil:
        pledge_names = [line.rstrip('\n') for line in fil]
    df_output['Pledge'] = pledge_names
    # count the number of interviews that each pledge has
    number_of_interviews = []
    for i in pledge_names:
        number_of_interviews.append(df_input["Pledge"].value_counts().get(i, 0))
    df_output['NumberOfInterviews'] = number_of_interviews
    # Get the Quality interview data
    number_of_quality_interviews = []
    for i in pledge_names:
        number_of_quality_interviews.append(get_quality_interviews(i, df_input))
    df_output["NQuality"] = number_of_quality_interviews
    df_output["PercentQuality"] = df_output["NQuality"] / df_output["NumberOfInterviews"] * 100
    return df_output


def brother_interview_rankings(df=None):
    """
    Returns a dataframe of interview rankings by brother
    :param df: Optional dataframe of interview rankings. Will read interviews.csv if none provided
    :return: pandas dataframe of interview rankings
    """
    if df is None:
        try:
            df = pd.read_csv('interviews.csv')
        except Exception as e:
            logger.error(f'error reading interviews.csv {e}')
            return 1
    df = df.drop(["Pledge", "Quality", "Time"], axis=1)
    grouped = df.groupby('Brother')
    counts = grouped.value_counts()
    counts = counts.sort_values(ascending=False)
    return counts
