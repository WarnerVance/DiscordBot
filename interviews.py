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
    :return: pandas dataframe of pledge interviews
    """
    try:
        if fn.check_pledge(pledge):
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

def interview_summary(df = None):
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
        number_of_interviews.append(df_input["Pledge"].value_counts().get(i,0))
    df_output['NumberOfInterviews'] = number_of_interviews
    # Get the Quality interview data
    number_of_quality_interviews = []
    for i in pledge_names:
        number_of_quality_interviews.append(get_quality_interviews(i, df_input))
    df_output["NQuality"] = number_of_quality_interviews
    df_output["PercentQuality"] = df_output["NQuality"]/df_output["NumberOfInterviews"]*100
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