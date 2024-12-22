import pandas as pd
import functions as fn
from logging_config import setup_logging

logger = setup_logging()

def add_interview(pledge, brother, quality, time):
    if pledge == '' or brother == '' or time == '':
        logger.error('empty field')
        return 1 
    if not fn.check_pledge(pledge):
        logger.error('pledge does not exist')
        return 1
    try:
        df = pd.read_csv('interviews.csv')
    except Exception:
       logger.error('error reading interviews.csv')
       return 1 
    try:
        if quality == '':
            quality = 'x'
        added_interview = [time, pledge, brother, quality]
        df.loc[len(df)] = added_interview
        return 0
    except Exception:
        logger.error('Error adding interview')
        return 1
def get_pledge_interviews(pledge):
    """
    Gets a dataframe of pledge interviews for a specific pledge
    :param pledge: Name of Pledge to check
    :return: pandas dataframe of pledge interviews
    """
    if fn.check_pledge(pledge):
        df = pd.read_csv('interviews.csv')
        return df.loc[df['pledge'] == pledge]
    else:
        return 1
