'''
Created on       29 Sep 2018
Last modified on 15 Oct 2018

@author: S.Walliser, P.Lucescu, F.Ferrari
'''

import argparse
import datetime as dt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from itertools import combinations
from nyse_holidays import get_nyse_holidays

def read_df_from_db(field_):
    '''Reads the csv file from the disk and returns a pandas dataframe, the
    content of the column 'Dates' is parsed as dates
    
    :param field_: [string] indicating the field, e.g "PX_LAST"
    
    :return df: [pandas.DataFrame] contaning the entire data set
    '''
#     field_ = "PX_LAST"
    # read csv file
    df = pd.read_csv(DIR_PATH + field_ + EXT, parse_dates=['Dates'])
    return df
pass

def read_industry_info():
    '''Reads the csv file containing the Bloomberg sector, industry group and
    subgroup for all the current S&P500 companies and returns a pandas dataframe
    containing the mentioned data
    
    :return sector_df: [pandas.DataFrame] containing sector, industry group and
        industry subgroup information
    '''
    # read csv file
    sector_df = pd.read_csv(DIR_PATH + 'SECTOR' + EXT)
    return sector_df
pass

def get_industry_groups():
    '''Returns the Bloomberg industry groups
    
    :return : [array] of Bloomberg industry groups 
    '''
    # call function `read_industry_info`
    group_df = read_industry_info()
    # return unique values only
    return np.unique(group_df.loc[1])
pass

def get_industry_sector():
    '''Returns the Bloomberg industry sector
    
    :return : [array] of Bloomberg industry sectors 
    '''
    # call function `read_industry_info`
    sector_df = read_industry_info()
    # return unique values only
    return np.unique(sector_df.loc[0])
pass

def get_tickers_list_by_ind_sec(ind_sec_):
    '''Given the Bloomberg industry sector the function returns all the
    Bloomberg tickers of the S&P 500 companies within the sector
    
    :param ind_sec_: [string] representing the Bloomberg sector
    
    :return tickers_list: [list of strings] containing Bloomberg tickers
    '''
#     ind_sec_ = "Communications"
    # read industry information
    sector_df = read_industry_info()
    # get indexes of companies within the desired sector
    idx = sector_df.iloc[0,:] == ind_sec_
    # define ticker list
    tickers_list = sector_df.columns.values[idx].tolist()
    return tickers_list
pass

def get_log_returns(prices_df_):
    '''Function which returns a dataframe with log returns for a given prices
    dataframe
    
    :param prices_df_: [pandas.DataFrame] with prices
    
    :return log_returns: [pandas.DataFrame] with log returns
    '''
    # copy prices dataframe
    log_returns = prices_df_.copy()
    # calculate log returns
    log_returns.iloc[:,1:] = np.log(prices_df_.iloc[:, 1:]) - \
        np.log(prices_df_.iloc[:, 1:].shift(1))
    return log_returns.fillna(value=0)
pass

def get_df_from_to(df_, date_from_, date_to_,
                   ind_sec_ = None,
                   tickers_list_ = None):
    '''Returns dataframe between and included two specific dates, and optionally
    only desired companies by specifying Bloomberg tickers list or only the
    companies within one specific sector
    
    :param df_: [pandas.DataFrame] where to select data from
    :param date_from_: [datetime.date] indicating date from when to select data
    :param date_to_: [datetime.date] indicating date to when select data
    :param ind_sec_: [string] indicating the Bloomberg sector, set to `None` by 
        default
    :param tickers_list_: [list of strings] indicating the Bloomberg sector,
        set to `None` by default
    
    :retrun sel_df: [pandas.DataFrame] with selected data
    '''
#     date_from_ = dt.date(2010, 1, 1)
#     date_to_ = dt.date(2010, 1, 15)
#     ind_group_ = "Electronics"
    # define indexes of dates
    idx_start = df_.index[df_['Dates'] == date_from_]
    idx_end = df_.index[df_['Dates'] == date_to_]
    # define the selected dataframe
    if tickers_list_ is not None:
        sel_df = df_.loc[idx_start[0]:idx_end[0]][['Dates'] + tickers_list_]
    elif ind_sec_ is not None:
        tickers_list = get_tickers_list_by_ind_sec(ind_sec_)
        sel_df = df_.loc[idx_start[0]:idx_end[0]][['Dates'] + tickers_list]       
    else:
        sel_df = df_.loc[idx_start[0]:idx_end[0]]
    # drop columns containing NaN (stocks that were not traded during the period
    # are removed)
    sel_df = sel_df.dropna(axis=1)
    return sel_df
pass

def get_normalized_df(df_):
    '''Return dataframe normalized to the first date
    
    :param df_: [pandas.DataFrame] with data
    
    :return norm_df: [pandas.DataFrame] with normalized data
    '''
    # copy input dataframe
    norm_df = df_.copy()
    # normalize dataframe to first day in the period
    norm_df.iloc[:,1:] = norm_df.iloc[:,1:]/norm_df.iloc[0,1:]*100
    return norm_df
pass
    
def get_x_trading_day(date_, trad_days_):
    '''Returns trading date `trad_days_` from or before `date_`
    
    :param date_: [datetime.date] trading date to add or subtract trading days
    :param trad_days_: [integer] trading days to add (+) or subtract (-)
    
    :return : [datetime.date] trading date which has been offset
    '''
    # define NYSE holidays from 2010 to 2018 (observation period)
    NYSE_HOLIDAYS = get_nyse_holidays(2010, 2018)
    # offset date
    output_date = np.busday_offset(date_, trad_days_, holidays = NYSE_HOLIDAYS)
    return output_date.astype(dt.date)
pass

def get_pairs_ind_sec(df_, date_from_, date_to_, ind_sec_):
    '''Forming all the possible pairs within one specific sector and between
    two specific dates
    
    :param df_: [pandas.DataFrame] with data
    :param date_from_: [datetime.date] indicating date from when to select data
    :param date_to_: [datetime.date] indicating date to when select data
    :param ind_sec_: [string] representing the sector
    
    :return pairs_list: [list of string] containing all the pairs combinations
        together with distance measures
    '''
#     date_from_ = dt.date(2010, 1, 1)
#     date_to_ = dt.date(2010, 1, 15)
#     ind_gr_sec_ = "Electronics"
    # getting the dataframe from `date_from_` to `date_to_`
    sel_df = get_df_from_to(df_, date_from_, date_to_, ind_sec_)
    # normalize selected dataframe
    norm_df = get_normalized_df(sel_df)
    # define all possible combination in a list of tuples
    pairs_list = list(combinations(list(norm_df.columns.values)[1:],2))
    for i, pair in enumerate(pairs_list):
        # calculate standard deviation
        criterium = np.std(norm_df[pair[0]] - norm_df[pair[1]])
        # add standard deviation info to the tuple
        pairs_list[i] = pairs_list[i] + (criterium,)
    return pairs_list
pass

def get_trad_schedule(df_,
                      trad_date_from_,
                      trad_date_to_,
                      est_per_days_,
                      trad_per_days_):
    '''Function which creates the trading schedule depending on the length of
    the desired formation period and trading period, as well as the start and
    end date of trading
    
    :param df_: [pandas.DataFrame] with data
    :param trad_date_from_: [datetime.date] first day of trading (trading date)
    :param trad_date_to_: [datetime.date] last day of trading (trading date)
    :param est_per_days_: [integer] formation period length in trading days
    :param trad_per_days_: [integer] trading period length in trading days
    
    :return trad_dates: [list of tuples] representing the trading schedule
    '''
#     est_per_days_ = 21 * 12
#     trad_per_days_ = 21 * 6
#     trad_date_from_ = dt.date(2011, 2, 1)
#     trad_date_to_ = dt.date(2018, 2, 1)
    # define first and last date in the data
    first_date_data = df_.iloc[0,0].to_pydatetime().date()
    end_date_data = df_.iloc[-1,0].to_pydatetime().date()
    # check whether the last trading date is smaller than last date in the data
    assert trad_date_to_ <= end_date_data, 'Last trading date is after last '\
        'date in the data'
    # check whether the last trading date is smaller than last date in the data
    assert get_x_trading_day(trad_date_from_, \
                             -(est_per_days_+1)) >= first_date_data, 'First ' \
        'formation period date is before the first date in the data'
    date = trad_date_from_
    # define list of tuples with the first trading period
    trad_dates = [tuple((date,
                         get_x_trading_day(date, trad_per_days_)))]
    # define all subsequent trading periods
    while trad_dates[-1][1] < trad_date_to_:
        # define next period start date
        trad_date_start = trad_dates[-1][1]
        # define next period end date
        if get_x_trading_day(trad_date_start, trad_per_days_) >= trad_date_to_:
            trad_date_end = trad_date_to_
        else:
            trad_date_end = get_x_trading_day(trad_date_start, trad_per_days_)
        # append the tuple with next period to `trad_dates`
        trad_dates.append(tuple((trad_date_start, trad_date_end)))
    return trad_dates
pass

def get_selected_pairs(df_, date_from_, date_to_, no_pairs_):
    '''Function which returns a list of triples containing the tickers and the
    distance measure for a specified number of pairs (`no_pairs_`)
    
    :param df_: [pandas.DataFrame] with data
    :param date_from_: [datetime.date] first day of formation (trading date)
    :param date_to_: [datetime.date] last day of formation (trading date)
    :param no_pairs_: [integer] number of pairs
    
    :return pairs_selected: [list of triples] with pairs tickers and historical
        standard deviation during the formation period
    '''
#     date_from_ = dt.date(2010, 1, 4)
#     date_to_ = get_x_trading_day(date_from_, 252)
#     no_pairs_ = 2
    # get all sectors
    sectors = get_industry_sector()
    # define empty list
    pairs_list = []
    # iterate over sectors
    for sector in sectors:
        # append to list of pairs new pairs
        pairs_list += get_pairs_ind_sec(df_, date_from_, date_to_, sector)
    # sort pairs lower std first
    pairs_list_sorted = sorted(pairs_list, key = lambda x: x[2])
    # select desired number of pairs only
    pairs_selected = pairs_list_sorted[0:no_pairs_]
    return pairs_selected
pass

def get_postions_pair(df_, date_from_, date_to_, pair_):
    '''Function that returns the positions for the two stocks in the pair over 
    the desired trading period
    
    :param df_: [pandas.DataFrame] with data
    :param date_from_: [datetime.date] first date in the period (trading date)
    :param date_to_: [datetime.date] last date in the period (trading date)
    :param pair_: [triple] including the two stocks forming the pair and the
        historical standard deviation of the spread between the two normalized
        stock time series
        
    :return : [pandas.DataFrame] with positions
    '''
#     date_from_ = get_x_trading_day(dt.date(2010, 1, 4), 252 + 1)
#     date_to_ = get_x_trading_day(date_from_, 126)
#     pair_ = ('ED US Equity', 'XEL US Equity', 1.348713804343775)
    # define debug message
    debug_msg = 'Getting positions for pair {} and {}'.format(pair_[0],
                                                              pair_[1])
    # print debug message
    print(debug_msg)
    # get dataframe for specific pair
    pair_df = get_df_from_to(df_, date_from_, date_to_,
                             tickers_list_ = list(pair_[0:2]))
    # normalize dataframe
    norm_pair_df = get_normalized_df(pair_df)
    # take difference between the two prices time series and define new column
    norm_pair_df['diff'] = norm_pair_df.iloc[:,1] - norm_pair_df.iloc[:,2]
    # define column absolute difference greater equal 2*std
    norm_pair_df['abs_diff_ge_std'] = np.abs(norm_pair_df.iloc[:,3]) >= 2 * \
        pair_[2]
    # set column with trade open to false
    norm_pair_df['trade_open'] = np.zeros(norm_pair_df.shape[0], dtype=bool)
    for i in range(norm_pair_df.shape[0]-1):
        if i == 0:
            continue
        # set remaining `trade_open` column to true as soon as the spread widens
        # (+1 since we are checking at the close of trading)
        if norm_pair_df.iloc[i, 4]:
            norm_pair_df.iloc[i+1:, 5] = True
        # set the remaining `trade_open` column to false as soon as the
        # difference changes of sign (+1 since we are checking at the close of
        # trading)
        if np.sign(norm_pair_df.iloc[i-1,3]) != np.sign(norm_pair_df.iloc[i,3]):
            norm_pair_df.iloc[i+1:, 5] = False
            # change sign of the i entry since it will be used to determine
            # whether the position was short or long 
            norm_pair_df.iloc[i,3] *= -1
    # define positions column names
    col_pos_names = [ticker + ' Pos' for ticker in pair_[0:2]]
    # define positions in the stocks, if Stock_1 - Stock_2 < 0 (see `diff`
    # column) Stock_2 is the winner (we need to go short) and Stock_1 is the
    # loser(we need to go long), and viceversa
    norm_pair_df[col_pos_names[0]] = np.sign(norm_pair_df['diff']) * \
        -1 * norm_pair_df['trade_open']
    norm_pair_df[col_pos_names[1]] = np.sign(norm_pair_df['diff']) * \
        norm_pair_df['trade_open']
    
    # plot for analysis, can be commented
#     plt.figure()
#     plt.plot(norm_pair_df['Dates'], norm_pair_df[pair_[0]]/100)
#     plt.plot(norm_pair_df['Dates'], norm_pair_df[pair_[1]]/100)
#     plt.plot(norm_pair_df['Dates'], norm_pair_df[col_pos_names[0]])
#     plt.plot(norm_pair_df['Dates'], norm_pair_df[col_pos_names[1]])
    return norm_pair_df[['Dates', col_pos_names[0], col_pos_names[1]]]
pass

def merge_positions_df(tot_pos_df_, pair_pos_df_):
    '''Function that merges two dataframes containing the positions on the
    different stocks 
    
    :param tot_pos_df_: [pandas.DataFrame] larger dataframe containing the 
        postions on the stocks
    :param pair_pos_df_: [pandas.DataFrame] smaller dataframe with the positions
        on the stocks for the subsequent period
    
    return tot_pos_df: [pandas.DataFrame] merged dataframe
    '''
    # copy total positions dataframe
    tot_pos_df = tot_pos_df_.copy()
    # define postions names
    col_tot_pos_df = tot_pos_df.columns.values[1:]
    col_pair_pos_df = pair_pos_df_.columns.values[1:]
    for col_pair_pos in col_pair_pos_df:
        # if position in one stock is already open, add positions
        if col_pair_pos in col_tot_pos_df:
            tot_pos_df[col_pair_pos] += pair_pos_df_[col_pair_pos]
        # if not add column
        else:
            tot_pos_df[col_pair_pos] = pair_pos_df_[col_pair_pos]
    return tot_pos_df
pass

def get_df_tot_positions(df_, 
                         trad_date_from_, 
                         trad_date_to_,
                         est_per_trad_days_,
                         no_pairs_):
    '''Functions which returns the total positions dataframe for one trading
    period, given the formation period length and the desired number of pairs
    
    :param df_: [pandas.DataFrame] with entire dataset
    :param trad_date_from_: [datetime.date] first date in the period (trading
        date)
    :param trad_date_to_: [datetime.date] last date in the period (trading date)
    :param est_per_trad_days_: [integer] formation period length in trading days
    :param no_pairs_: [integer] number of pairs to trade on
    
    :return tot_pos_df: [pandas.DataFrame] containg all the positions 
    '''
#     trad_date_from_ = dt.date(2011, 2, 1)
#     trad_date_to_ = get_x_trading_day(trad_date_from_, 126)
#     est_per_trad_days_ = 252
#     no_pairs_ = 50
    # define formation period start and end dates
    est_date_from = get_x_trading_day(trad_date_from_,
                                      -(est_per_trad_days_+1))
    # formation period end one trading day before beginning of the trading
    # period
    est_date_to = get_x_trading_day(trad_date_from_, -1)
    # define debug message
    debug_msg = 'Estimating from {} to {}'.format(est_date_from, est_date_to)
    # print debug message
    print(debug_msg)
    # get selected pairs
    pairs_selected = get_selected_pairs(df_, 
                                        est_date_from, 
                                        est_date_to, 
                                        no_pairs_)
    # define debug message
    debug_msg = 'Trading from {} to {}'.format(trad_date_from_, trad_date_to_)
    # print debug message
    print(debug_msg)
    # define a dataframe with the positions
    tot_pos_df = get_postions_pair(df_,
                                   trad_date_from_,
                                   trad_date_to_,
                                   pairs_selected[0])
    # iterate over all selected pairs and merge `pair_pos_df` dataframe with
    # `tot_pos_df`
    for sel_pair in pairs_selected[1:]:
        # get positions for one pair
        pair_pos_df = get_postions_pair(df_,
                                        trad_date_from_,
                                        trad_date_to_,
                                        sel_pair)
        # merge dataframes
        tot_pos_df = merge_positions_df(tot_pos_df, pair_pos_df)
    return tot_pos_df
pass

def simulate_trading(totret_df_,
                     trad_date_from_,
                     trad_date_to_,
                     est_per_trad_days_,
                     trad_per_trad_days_,
                     no_pairs_):
    '''Function that returns the positions in the single stocks for each trading
    day in the trading period
    
    :param totret_df_: [pandas.DataFrame] with the total return index data
    :param trad_date_from_: [datetime.date] first day of trading (trading date)
    :param trad_date_to_:[datetime.date] last day of trading (trading date)
    :param est_per_days_: [integer] formation period length in trading days
    :param trad_per_days_: [integer] trading period length in trading days
    :param no_pairs_: [integer] number of pairs to trade on
    
    :return trad_period_positions: [pandas.DataFrame] with the positions in the
        single stocks for each trading day in the trading period
    '''
    # define trading schedule
    trad_periods = get_trad_schedule(totret_df_,
                                     trad_date_from_,
                                     trad_date_to_,
                                     est_per_trad_days_,
                                     trad_per_trad_days_)
    # get first trading sub-period positions
    trad_period_pos = get_df_tot_positions(totret_df_,
                                                 trad_periods[0][0],
                                                 trad_periods[0][1],
                                                 est_per_trad_days_,
                                                 no_pairs_)
    # iterate over all remaining trading sub-periods
    for trad_period in trad_periods[1:]:
        # get sub period positions
        sub_period_pos = get_df_tot_positions(totret_df_,
                                              trad_period[0],
                                              trad_period[1],
                                              est_per_trad_days_,
                                              no_pairs_)
        # append the `sub_period_pos` to `trad_period_pos` (we skip first row 
        # since no position is open on the first day of the new period)
        trad_period_pos = trad_period_pos.append(sub_period_pos[1:])
    # fill NaN values with zeros
    trad_period_pos = trad_period_pos.fillna(value=0)
    print('Done')
    return trad_period_pos
pass

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # define arguments parser
    parser = argparse.ArgumentParser(description = 'Arguments of the Backtest')
    # adding arguments
    parser.add_argument('-formation_period_length',
                        dest='est_per_trad_days',
                        type=int,
                        help='Length of the formation period')
    parser.add_argument('-trading_period_length',
                        dest='trad_per_trad_days',
                        type=int,
                        help='Length of the trading period')
    parser.add_argument('-number_of_pairs',
                        dest='no_pairs',
                        type=int,
                        help='Number of pairs')
    parser.add_argument('-start_date',
                        dest='trad_date_from',
                        type=str,
                        help='First trading date')
    parser.add_argument('-end_date',
                        dest='trad_date_to',
                        type=str,
                        help='Last trading date')
    # parsing arguments
    args = parser.parse_args()
    
    #---------------------------------------------------------------------------
    
    # define global variables
    DIR_PATH = ''
    EXT = '.csv'
    
    # deading data
    close_df = read_df_from_db('PX_LAST')
    totret_df = read_df_from_db('TOT_RETURN_INDEX_GROSS_DVDS')
    # define 
    trad_date_from = dt.datetime.strptime(args.trad_date_from,'%Y-%m-%d').date()
    trad_date_to = dt.datetime.strptime(args.trad_date_to,'%Y-%m-%d').date()
#     est_per_trad_days = 252
#     trad_per_trad_days = 126
#     no_pairs = 20
#     trad_date_from = dt.date(2011, 2, 1)
#     trad_date_to = dt.date(2014, 1, 31)
    # get postions dataframe
    positions_df = simulate_trading(totret_df,
                                    trad_date_from,
                                    trad_date_to,
                                    args.est_per_trad_days,
                                    args.trad_per_trad_days,
                                    args.no_pairs)
    # define dates
    dates = positions_df["Dates"]
    # define dataframe without dates
    positions_wd_df = positions_df.drop(["Dates"], 1)
    # define ticker list in scope of trading
    ticker_list = [ticker[:-4] for ticker in positions_wd_df.columns]
    # redefine column names
    positions_wd_df.columns = ticker_list
    # define open positions each day
    open_pos = np.array(np.sum(np.abs(positions_wd_df), axis=1))
    open_pos[open_pos == 0] = 1
    open_pos_mat = np.transpose(np.tile(open_pos, (positions_wd_df.shape[1],1)))
    # define weight for each day
    positions_wd_df = positions_wd_df/open_pos_mat
    new_positions_df = pd.concat([dates, positions_wd_df], axis = 1)
     
    # get prices for the period and ticker list
    prices = get_df_from_to(totret_df, trad_date_from, trad_date_to,
                            tickers_list_= ticker_list)
    # calculate log returns
    log_returns = get_log_returns(prices)
    # convert them to simple returns
    ordinary_returns = np.exp(log_returns.iloc[:,1:]) - 1
    # sum up returns and calculate cumulative sum of log returns
    weighted_log_returns_cum_sum = np.cumsum(np.log(
        np.sum(ordinary_returns * new_positions_df,
               axis = 1)+1))
    # converto to simple return
    weigthed_ordinary_returns_cum_sum = np.exp(weighted_log_returns_cum_sum)
    # plot
    plt.figure()
    plt.plot(prices['Dates'], weigthed_ordinary_returns_cum_sum)
