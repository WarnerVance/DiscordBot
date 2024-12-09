import logging

# Define custom logging level for command tracking
COMMAND_LEVEL = 25  # Set between INFO (20) and WARNING (30)
logging.addLevelName(COMMAND_LEVEL, 'COMMAND')

# Add custom command logging method to Logger class
def command(self, message, *args, **kwargs):
    if self.isEnabledFor(COMMAND_LEVEL):
        self._log(COMMAND_LEVEL, message, args, **kwargs)
logging.Logger.command = command

def setup_logging():
    # Configure logging system with both file and console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),   # Log to file
            logging.StreamHandler()           # Log to console
        ]
    )
    return logging.getLogger('discord_bot') 