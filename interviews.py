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
        df.to_csv('interviews.csv', index=False)
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
    try:
        if fn.check_pledge(pledge):
            df = pd.read_csv('interviews.csv')
            return df.loc[df['Pledge'] == pledge]
        else:
            return 1
    except Exception:
        logger.error('error getting pledge')
        return 1
def get_brother_interviews(brother):
    try:
        df = pd.read_csv('interviews.csv')
        return df.loc[df['Brother'] == brother]
    except Exception:
        logger.error('error getting brother')

def interview_rankings():
    try:
        df = pd.read_csv('interviews.csv')
    except Exception:
        logger.error('error reading interviews.csv')
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
    if fn.check_pledge(pledge):
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
