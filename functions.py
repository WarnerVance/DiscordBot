import pandas as pd 
import time

def check_pledge(name):
    with open('pledges.csv', 'r') as fil:
        pledge_names = [line.rstrip('\n') for line in fil]
        if name in pledge_names:
            return True
        else:
            return False

def get_points_csv():
    df = pd.read_csv("Points.csv")
    return df

def update_points(name, point_change):
    if check_pledge(name):
        df = get_points_csv()
        df.loc[len(df)] = [time.time(), name, point_change]
        df.to_csv("Points.csv", index=False)
        result = 0
    else:
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
    # Get all pledges and their points
    pledges = get_pledges()
    pledge_points = []
    for pledge in pledges:
        points = get_pledge_points(pledge)
        pledge_points.append((pledge, points))
    
    # Sort by points in descending order
    ranked_pledges = sorted(pledge_points, key=lambda x: x[1], reverse=True)
    
    # Format into list of strings
    formatted_rankings = []
    for i, (pledge, points) in enumerate(ranked_pledges, 1):
        formatted_rankings.append(f"{i}. {pledge}: {points} points")
        
    return formatted_rankings

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

