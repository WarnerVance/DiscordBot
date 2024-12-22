import pandas as pd
import functions as fn
def add_interview(pledge, brother, quality, time):
    if pledge == '' or brother == '' or time == '':
        logger.error('empty field')
        return 1 
    if not fn.check_pledge(pledge):
        logger.error('pledge does not exist')
        return 1
    try:
        df = pd.read_csv('interviews.csv')
    except:
       logger.error('error reading interviews.csv')
       return 1 
    try:
        if quality == '':
            quality = 'x'
        added_interview = [time, pledge, brother, quality]
        df.loc[len(df)] = added_interview
        return 0
    except:
        logger.error('error adding interview')
        return 1
