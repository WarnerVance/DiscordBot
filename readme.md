# Pledge Points Discord Bot

A Discord bot for managing pledge points and rankings.

## Features

- Add/remove pledges
- Update pledge points with comments
- View pledge rankings and point distributions
- Generate graphs showing point distributions and history
- Automated daily updates
- Comprehensive logging and status monitoring
- Approval system for point changes

## Commands

### Pledge Management
- `/add_pledge` - Add a new pledge to the list
- `/remove_pledge` - Remove a pledge from the list
- `/list_pledges` - Get list of all pledges

### Points Management  
- `/get_pledge_points` - Get points for a specific pledge
- `/change_pledge_points` - Update points for a specific pledge
- `/show_points_graph` - Display current points distribution graph
- `/show_pledge_ranking` - Display current pledge rankings
- `/show_points_history` - Display points progression over time
- `/export_points_file` - Export points data as CSV
- `/approve_points` - Approve pending point changes
- `/reject_points` - Reject pending point changes
- `/pending_points` - View all pending point changes

### System Commands
- `/status` - Get bot and server status information
- `/log_size` - Get size of bot's log file
- `/show_logs` - View recent bot logs
- `/shutdown` - Safely shutdown the bot (Admin only)

## Requirements

- Python 3.8+
- discord.py
- Other dependencies listed in requirements.txt

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure bot token in environment variables
4. Run the bot: `python main.py`

## Notes

- Brother role required to use commands
- Points changes limited to ±35 points per update
- Daily updates posted at 5:00 and 6:00 UTC
- Comprehensive error handling and logging
- Point changes require approval from a second Brother
- Pending changes expire after 24 hours if not approved/rejected
