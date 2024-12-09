# Pledge Bot Technical Documentation

## System Overview

### Main Components
- Discord bot using discord.py library
- Simple CSV file storage (pledges.csv)
- Command handling system
- Permission checking
- Activity logging

### Core Functions

#### Starting the Bot
- Sets up basic Discord permissions
- Creates secure connection
- Loads and syncs available commands

#### Command System
1. Role Checker:
   - Makes sure user has "Brother" role
   - Sends error if role missing
   - Only visible to command user

2. Command Timeout:
   - Stops commands that take too long
   - 10 second default limit
   - Tells user if command timed out

3. Command Logger:
   - Records who uses what commands
   - Saves when and where commands are used
   - Helps track issues

4. Name Suggestions:
   - Shows pledge names while typing
   - Limited to 25 suggestions
   - Not case sensitive

### Data Storage
- Uses simple CSV file
- One pledge per line
- Updates file safely
- Keeps copy in memory for speed

### Safety Features
- Checks for Brother role
- Cleans up user input
- Limits how often commands can be used
- Keeps bot token secure

### Logging
- Different levels of detail
- Creates new files when old ones get big
- Records important details about errors
- Tracks command usage
- Delete's after 3 days during midnight update

### Error Management
- Catches and handles errors
- Tells users what went wrong
- Tries to reconnect if disconnected
- Retries failed file operations

### Speed and Performance
- Handles multiple commands at once
- Reuses connections when possible
- Saves frequently used data
- Cleans up unused resources

### Regular Tasks
1. Managing log files
2. Backing up pledge data
3. Updating available commands
4. Checking system health

## Development Guide

### Adding Commands
1. Write the command function
2. Add required checks:
   ```python
   @bot.tree.command()
   @log_command()
   @timeout_command()
   ```
3. Check for Brother role
4. Handle possible errors
5. Update command list

### Testing
- Test command functions
- Test Discord connection
- Test role checking
- Test error handling

### Setting Up Bot
1. Check code is up to date
2. Run all tests
3. Set up bot token
4. Update Discord permissions
5. Check logging works

## Common Problems

### Frequent Issues
1. Commands Not Working
   - Check Discord status
   - Check bot permissions
   - Look for command changes

2. Data Problems
   - Check file access
   - Check storage space
   - Make sure CSV file looks right

3. Role Problems
   - Check Discord roles
   - Check server settings
   - Make sure role names match

### Finding Problems
1. Turn on detailed logging
2. Check computer resources
3. Test Discord connection
4. Look at recent logs
5. Check pledge data file

