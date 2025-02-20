import os
import time

import pandas as pd

from CheckRoles import check_pledge
from logging_config import setup_logging

logger = setup_logging()


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
    plt.figure(figsize=(10, 5))
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
    Adds a record of pending point changes to the file "PendingPoints.csv". This function helps to
    document the adjustments in points for the specified individual. It logs the event with details
    such as the timestamp, individual's name, the point change amount, comments justifying the change,
    and the requester of the operation.

    :param name: A string indicating the pledges name whose points are to be modified.
    :param point_change: An integer specifying the points to be added (positive) or removed (negative).
    :param comment: A string providing additional information or justification for the point change.
    :param requester: A string representing the name or identifier of the user requesting the change.
    :return: An integer result. Returns 0 on successful addition and 1 in case of failure.
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
            return False, f"Invalid index: {index}. Valid range is 0-{len(df_pending) - 1}", {}

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
    Rejects a pending point from the CSV file at the specified index. If the index is invalid, an
    error message and an empty dictionary will be returned. If the operation is successful, the
    pending point will be removed from the file, and the operation details will be returned.

    :param index: The index in the pending points DataFrame corresponding to the point to reject.
                  Must be within the valid range of indices for the DataFrame.
    :type index: int
    :return: A tuple consisting of three elements:
             - A boolean indicating the success of the operation.
             - A message string providing details about the operation or error.
             - A dictionary of the rejected point's data if successful or an empty dictionary on failure.
    :rtype: tuple[bool, str, dict]
    """
    try:
        df_pending = get_pending_points_csv()

        # Validate index
        if index < 0 or index >= len(df_pending):
            return False, f"Invalid index: {index}. Valid range is 0-{len(df_pending) - 1}", {}

        point_data = df_pending.iloc[index].to_dict()
        df_pending = df_pending.drop(index)
        df_pending.to_csv("PendingPoints.csv", index=False)
        return True, "Points rejected", point_data

    except Exception as e:
        logger.error(f"Error rejecting points: {str(e)}")
        return False, f"Error: {str(e)}", {}
