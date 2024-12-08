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

def update_points(name, point_change, comment=None):
    try:
        if check_pledge(name):
            df = get_points_csv()
            new_row = {
                "Time": time.time(),
                "Name": name,
                "Point_Change": point_change,
                "Comments": comment if comment is not None else ""
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv("Points.csv", index=False)
            result = 0
        else:
            result = 1
    except Exception as e:
        logger.error(f"Error in update_points: {str(e)}")
        result = 1
    return result


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
        # Get all pledges and their points
        pledges = get_pledges()
        pledge_points = []
        df = get_points_csv()
        
        for pledge in pledges:
            points = get_pledge_points(pledge)
            # Get the most recent comment
            pledge_df = df[df["Name"] == pledge]
            recent_comment = ""
            if not pledge_df.empty:
                last_comment = pledge_df.iloc[-1]["Comments"]
                # Check if comment is not empty or NaN
                if pd.notna(last_comment) and str(last_comment).strip():
                    recent_comment = last_comment
            pledge_points.append((pledge, points, recent_comment))
        
        # Sort by points in descending order
        ranked_pledges = sorted(pledge_points, key=lambda x: x[1], reverse=True)
        
        # Format into list of strings
        formatted_rankings = []
        for i, (pledge, points, comment) in enumerate(ranked_pledges, 1):
            comment_text = f" ({comment})" if comment else ""
            formatted_rankings.append(f"{i}. {pledge}: {points} points{comment_text}")
            
        return formatted_rankings
    except Exception as e:
        logger.error(f"Error in get_ranked_pledges: {str(e)}")
        return ["Error retrieving rankings"]

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

