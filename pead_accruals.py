'''
Created on Tue 9 June 2020, 1:23am

@author: brandon
'''
###--------------
import pandas as pd
from datetime import datetime
import dateutil.relativedelta
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None
###--------------

def reading_data(start_date,end_date):
    fundamentals = pd.read_csv('US_Financials.csv')
    e_hist = pd.read_csv('US_earnings_History.csv')

    e_hist['surprisePercent'] = e_hist['epsDifference'] / e_hist['epsEstimate'] * 100 
    e_hist.dropna(axis=0,subset=['epsActual','epsEstimate','surprisePercent'],inplace=True)
    e_hist[["reportDate", "date"]] = e_hist[["reportDate", "date"]].apply(pd.to_datetime)

    e_hist = e_hist[(e_hist['reportDate'] >= start_date) & (e_hist['reportDate'] <= end_date)]
    valid_tickers = e_hist.groupby('Ticker').count()['reportDate'].reset_index()
    tickers = valid_tickers[valid_tickers['reportDate'] >= 5]['Ticker']
    e_hist_final = e_hist[e_hist['Ticker'].isin(tickers)]

    core = fundamentals[['Ticker','flag','date',
                    'totalCashflowsFromInvestingActivities',
                     'totalCashFromFinancingActivities',
                    'totalCashFromOperatingActivities',
                     'totalStockholderEquity',
                     'depreciation',
                     'dividendsPaid',
                    'netIncome_x',
                    ]]

    core['totalCashflowsFromInvestingActivities'] = core.groupby('Ticker')['totalCashflowsFromInvestingActivities'].ffill()
    core['totalCashFromFinancingActivities'] = core.groupby('Ticker')['totalCashFromFinancingActivities'].ffill()
    core['totalCashFromOperatingActivities'] = core.groupby('Ticker')['totalCashFromOperatingActivities'].ffill()
    core['totalStockholderEquity'] = core.groupby('Ticker')['totalStockholderEquity'].ffill()
    core['depreciation'] = core.groupby('Ticker')['depreciation'].ffill()
    core['dividendsPaid'] = core.groupby('Ticker')['dividendsPaid'].ffill()
    core['netIncome_x'] = core.groupby('Ticker')['netIncome_x'].ffill()
    core.dropna(inplace=True)
    core['ChangeInCash'] = core['totalCashFromOperatingActivities'] + core['totalCashFromFinancingActivities'] + core['totalCashflowsFromInvestingActivities']
    core['WC'] = core['netIncome_x'] + core['depreciation'] - core['totalCashFromOperatingActivities']
    core['NCO'] = core['netIncome_x'] - core['totalCashFromOperatingActivities'] - core['totalCashflowsFromInvestingActivities']
    core['TACC'] = core['netIncome_x'] - core['ChangeInCash'] - core['dividendsPaid']
    core['ACC_Income'] = core['TACC']/core['netIncome_x']
    core[['date']] = core[['date']].apply(pd.to_datetime)

    ava_tickers = e_hist_final['Ticker'].unique()
    working_df = core[(core['Ticker'].isin(ava_tickers)) & (core['date'] >= start_date) & (core['date'] <= end_date)]

    working_df['month'] = working_df['date'].dt.month
    working_df['year'] = working_df['date'].dt.year
    e_hist_final['month'] = e_hist_final['reportDate'].dt.month
    e_hist_final['year'] = e_hist_final['reportDate'].dt.year
    return e_hist_final,working_df

def get_returns(ticker,start_date,end_date,pos_type,price_df):
    '''
    Description
        1. This function calculates returns (simple)

    Params
        1. ticker - the ticker of interest
        2. start_date - the date position was opened
        3. end_date - the date position was closed
        4. pos_type - position type (long/short)
        5. price_df - dataframe with price data

    Returns
        1. returns, float (simple)
    '''
    try:
        p_1 = price_df[(price_df['Date']==start_date)]['Adjusted_close'].values[0]
        p_2 = price_df[(price_df['Date']==end_date)]['Adjusted_close'].values[0]
    except:
        return False
    if pos_type == 'long':
        returns = (p_2/p_1) - 1
    else:
        returns = -(p_2/p_1) + 1
    return returns

def generate_positions(e_hist_final,working_df,start_date,end_date,hold_duration='M'):
    '''
    Description
    1. Constructs a dictionary to hold positions 
    2. Structure is as follows:
        key: date of position opened
        value: dictionary with the following structure:
            |-- key: long 
             -- value: list of tickers

            |-- key: short 
             -- value: list of tickers
    3. Constructs list containing all tickers of interest

    Params
        1. e_hist_final - DataFrame containing earnings
        2. working_df - DataFrame contain accruals
        3. hold_duration - timeframe for rebalancing (e.g 'M' - monthly, 'Q' - quarterly)
        4. start_date - beginning date of investment
        5. end_date - end date of investment
    
    Returns
        1. positions_dict
        2. rebalancing_dates
        3. all tickers
    '''

    rebalancing_dates = pd.date_range(start_date,end_date,freq=hold_duration)
    delta_dict = {
                'M':1,
                'Q':3
                }
    positions_dict = {}
    all_tickers = []
    for i in range(len(rebalancing_dates)-1):
        d = rebalancing_dates[i]
        d2 = d - dateutil.relativedelta.relativedelta(months=delta_dict[hold_duration])
        date = str(d.date())
        month1 = d.month
        year1 = d.year
        month2 = d2.month
        year2 = d2.year

        #estimates
        estimates_list = e_hist_final[(e_hist_final['month'] <= month1) & 
                                      (e_hist_final['year'] <= year1) &
                                      (e_hist_final['month'] >= month2) & 
                                      (e_hist_final['year'] >= year2)
                                     ]
        estimates_list.sort_values(by=['surprisePercent'],inplace=True,ascending=True)
        estimates_list.drop_duplicates(subset=['Ticker'],inplace=True,keep='last')
        tickers = estimates_list['Ticker']
        n = int(round(0.1 * len(estimates_list),0))

        #accruals
        accruals = working_df[(working_df['Ticker'].isin(tickers)) & (working_df['date'] <= d)]
        accruals = accruals[['Ticker','date','ACC_Income']]
        accruals.sort_values(by=['ACC_Income'],inplace=True,ascending=True)
        accruals.drop_duplicates(subset=['Ticker'],inplace=True,keep='last')

        #merging
        main = pd.merge(estimates_list,accruals,how='left',on='Ticker')
        long = main.sort_values(by=['surprisePercent','ACC_Income'],ascending=[False,True])
        short = main.sort_values(by=['surprisePercent','ACC_Income'],ascending=[False,False])
        
        #collecting the ticker to purhcase
        long = long[long['epsDifference'] > 0].head(n)['Ticker'].to_list()
        short = short[short['epsDifference'] < 0].head(n)['Ticker'].to_list()

        positions_dict[date] = {
                            'long':long,
                            'short':short
                            }
        for t in long:
            if t not in all_tickers:
                all_tickers.append(t)
        for s in short:
            if s not in all_tickers:
                all_tickers.append(s)
    return positions_dict,rebalancing_dates,all_tickers

def generate_price(positions_dict,rebalancing_dates,all_tickers):
    '''
    Description
        1. Constructs a dictionary containing DataFrames of price for optimized performance when backtesting

    Params
        1. positions_dict - from generate_positions
        2. rebalancing_dates - from generate_positions
        3. all_tickers - from generate_positions

    Returns
        1. price_dict
    '''
    p_df = pd.read_csv('US_price.csv')
    price = p_df[['Ticker','Adjusted_close','Date']]
    price[['Date']] = price[['Date']].apply(pd.to_datetime)
    start_date = rebalancing_dates[0]
    end_date = rebalancing_dates[-1]
    price = price[(price['Date']>=start_date) & (price['Date']<=end_date) & (price['Ticker'].isin(all_tickers))]
    price_dict = {}
    for t in all_tickers:
        temp = price[price['Ticker']==t]
        temp.set_index('Date',inplace=True)
        idx = pd.date_range(start_date,end_date)
        temp = temp.reindex(idx, method='ffill')
        temp.reset_index(inplace=True)
        temp.columns = ['Date','Ticker','Adjusted_close']
        temp.dropna(inplace=True)
        temp = temp[temp['Date'].isin(rebalancing_dates)]
        price_dict[t] = temp

    return price_dict

def backtest(positions_dict,price_dict,rebalancing_dates):
    '''
    Description
        1. Conducts backtesting

    Params
        1. positions_dict - from generate_positions
        2. rebalancing_dates - from generate_positions
        3. price_dict - dict containing dfs of prices

    Returns
        1. backtest_result - % performance of strategy
        2. total_dict - total performance over time
        3. long_dict - long performance over time
        4. short_dict - short performance over time
    '''

    backtest_result = 0.0
    long_dict = {}
    short_dict = {}
    total_dict = {}
    for i in range(len(rebalancing_dates)-1):
        
        d = str(rebalancing_dates[i].date())
        long = positions_dict[d]['long']
        short = positions_dict[d]['short']
        end_date = rebalancing_dates[i+1]
        total_positions = len(long) + len(short)

        if total_positions == 0:
            continue
        
        long_returns = 0
        short_returns = 0

        for stock in long:
            ret = get_returns(stock,d,end_date,'long',price_dict[stock])
            if ret == False:
                continue
            long_returns += ret
            
        for stock in short:
            ret = get_returns(stock,d,end_date,'short',price_dict[stock])
            if ret == False:
                continue
            short_returns += ret
        
        #containing the data
        if len(long) != 0:
            long_dict[i] = [d,long_returns/len(long)]
        if len(short) !=0:
            short_dict[i] = [d,short_returns/len(short)]
        
        backtest_result += (long_returns + short_returns)/total_positions
        
        total_dict[i] = [d,(long_returns + short_returns)/total_positions]
        
    return backtest_result,total_dict,long_dict,short_dict

def plot_backtest_results(total_dict,long_dict,short_dict):
    total = pd.DataFrame.from_dict(total_dict,orient='index',columns=['Date','Returns'])
    long = pd.DataFrame.from_dict(long_dict,orient='index',columns=['Date','Returns'])
    short = pd.DataFrame.from_dict(short_dict,orient='index',columns=['Date','Returns'])

    fig, ax1 = plt.subplots(figsize=(15,6))
    ax1.plot(total['Date'],total['Returns'].cumsum(),label='Combined Performance',marker='o')
    ax1.plot(long['Date'],long['Returns'].cumsum(),label='Long Performance',marker='o')
    ax1.plot(short['Date'],short['Returns'].cumsum(),label='Short Performance',marker='o')
    ax1.set_xlabel('Date Date')
    ax1.set_ylabel('Returns',color='black')
    plt.title('Porfolio Performance',color='black')
    ax1.legend(loc=0)
    plt.xticks(rotation=45, ha='right')
    plt.show()

###--Overview of functions--
'''
1. reading_data(start_date,end_date)
- Return: e_hist_final,working_df

2. get_returns(ticker,start_date,end_date,pos_type,price_df)
- Return: returns

3. generate_positions(e_hist_final,working_df,start_date,end_date,hold_duration='M')
- Return: positions_dict,rebalancing_dates

4. generate_price(positions_dict,rebalancing_dates)
- Return: price_dict

5. backtest(positions_dict,price_dict,rebalancing_dates)
- Return: backtest_result,total_dict,long_dict,short_dict

6. plot_backtest_results(total_dict,long_dict,short_dict)
- Return: None 
'''
###-----------End-----------

end_date = datetime.strptime('2020-01-01', '%Y-%m-%d')
start_date = datetime.strptime('2017-01-01', '%Y-%m-%d')

e_hist_final,working_df = reading_data(start_date,end_date)
positions_dict, rebalancing_dates,all_tickers = generate_positions(e_hist_final,working_df,start_date,end_date,hold_duration='M')
price_dict = generate_price(positions_dict, rebalancing_dates,all_tickers)
backtest_result,total_dict,long_dict,short_dict = backtest(positions_dict,price_dict,rebalancing_dates)

print("Backtest completed. Performance:{}%".format(round(backtest_result*100,5)))

plot_backtest_results(total_dict,long_dict,short_dict)
