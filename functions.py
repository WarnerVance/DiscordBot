import pandas as pd 
import time
import os
from datetime import datetime
from logging import getLogger

logger = getLogger(__name__)

def check_pledge(name):
    with open('pledges.csv', 'r') as fil:
        pledge_names = [line.rstrip('\n') for line in fil]
        if name in pledge_names:
            return True
        else:
            return False

def get_points_csv():
    try:
        if not os.path.exists("Points.csv"):
            # Create new DataFrame with all required columns
            df = pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
            df.to_csv("Points.csv", index=False)
        else:
            df = pd.read_csv("Points.csv")
            # Add Comments column if it doesn't exist
            if "Comments" not in df.columns:
                df["Comments"] = ""
                df.to_csv("Points.csv", index=False)
    except Exception as e:
        logger.error(f"Error in get_points_csv: {str(e)}")
        # Return empty DataFrame with correct columns if there's an error
        return pd.DataFrame(columns=["Time", "Name", "Point_Change", "Comments"])
    return df

def update_points(name: str, point_change: int, comment=None):
    """
    Update points for a pledge with comprehensive error handling and validation.
    
    Args:
        name (str): The name of the pledge
        point_change (int): The number of points to add/subtract
        comment (str, optional): A comment about the point change
        
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
            
        # Sanitize inputs
        name = name.strip()
        point_change = int(point_change)  # Convert float to int if necessary
        
        # Validate comment
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
            
        # Save to CSV with error handling
        try:
            # Create backup of current file
            if os.path.exists("Points.csv"):
                backup_name = f"Points_backup_{int(current_time)}.csv"
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


def get_pledge_points(name):
    if check_pledge(name):  # Simplified boolean comparison
        df = get_points_csv()
        points = df[df["Name"] == name]["Point_Change"].sum()
        return points  # Handle case when no points exist


def add_pledge(name):
    if check_pledge(name):
        return 1
    else:
        with open('pledges.csv', 'a') as fil:
            fil.write(f"{name}\n")
    return 0

def get_pledges():
    with open('pledges.csv', 'r') as fil:
        return [line.rstrip('\n') for line in fil]

def get_points_graph():
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
            
        pledge_points = []
        try:
            df = get_points_csv()
            if df.empty:
                logger.info("Points file is empty")
                # Still continue, as pledges might just have 0 points
        except Exception as e:
            logger.error(f"Error reading points CSV: {str(e)}")
            return ["Error reading points data"]
        
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
        
        if not pledge_points:
            return ["No valid pledge data found"]
            
        # Sort by points in descending order
        try:
            ranked_pledges = sorted(pledge_points, key=lambda x: (x[1], x[0].lower()), reverse=True)
            # Secondary sort by name if points are equal
        except Exception as e:
            logger.error(f"Error sorting pledges: {str(e)}")
            return ["Error sorting pledge rankings"]
        
        # Format into list of strings with max length protection
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
            
    return 0

def get_points_file():
    # Return the points file name
    return 'Points.csv'

def get_points_over_time():
    import matplotlib.pyplot as plt
    # Read points data and convert to pandas DataFrame
    df = pd.read_csv('Points.csv')
    
    # Convert timestamp to datetime
    df['Time'] = pd.to_datetime(df['Time'], unit='s')
    
    # Sort by time
    df = df.sort_values('Time')
    
    # Calculate running sum for each pledge
    pledges = get_pledges()
    plt.figure(figsize=(10, 6))
    
    for pledge in pledges:
        pledge_data = df[df['Name'] == pledge].copy()
        if not pledge_data.empty:
            pledge_data['Cumulative_Points'] = pledge_data['Point_Change'].cumsum()
            plt.plot(pledge_data['Time'], pledge_data['Cumulative_Points'], label=pledge, marker='o')
    
    plt.title('Pledge Points Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Points')
    plt.legend()
    plt.grid(True)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save and return filename
    filename = 'points_over_time.png'
    plt.savefig(filename)
    plt.close()
    return filename

def get_recent_logs(hours: int = 24) -> tuple[list[str], str]:
    """
    Retrieve logs from the past specified hours.
    Returns tuple of (log_lines, error_message).
    If error_message is not empty, log_lines will be empty.
    """
    try:
        now = time.time()
        past_time = now - (hours * 60 * 60)
        
        if not os.path.exists('bot.log'):
            return [], "Log file does not exist."
            
        with open('bot.log', 'r') as f:
            logs = f.readlines()
            
        if not logs:
            return [], "Log file is empty."
            
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

