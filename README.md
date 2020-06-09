# Post Earnings Announcement Drift (PEAD) & Accrual Anomaly

This notebook aims to examine if the [Accrual anomaly (Balakrishnan Et al,2009)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1793364) and [PEAD (Dechow Et al, 2011)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1510321) still exist today. 

I've opted to exclude the months of COVID-19 due to extreme volatility in the market and influx of liquidity introduced.<br>
Due to data unavailability, the investigated timeframe is only from 1st Jan 2017 - 1st Jan 2020. <br>
The holding period for each stock will be monthly and the rebalancing is done at the end of each month. <br>
<br>

Given that [most fund managers lag index funds](https://www.marketwatch.com/story/why-way-fewer-actively-managed-funds-beat-the-sp-than-we-thought-2017-04-24), I thought SPY would be a good benchmark to compare the relative performance.

### Results 
#### Cumulative Performance
![](Images/cumulative_performance.png)

#### Non-cumulative Performance
![](Images/non_cumulative_performance.png)

#### Observations
1. The top 10% and bottom 10% of stocks appear to be inversely related between 2018-06 to 2019-01.
2. PEAD + Accruals underperforms, for when we factor in transaction costs, even if we only go long, the returns will be significant less than SPY. 
3. The strategy is missing key growth stocks (due to unavailable data) that have contributed to SPY's performance and thus when we include them, the results could change drastically. (Refer to Appendix A of the .ipynb )

Feel free to clone the repo and conduct your own investigation!

### Resources required to replicate findings
1. Fundamental data - cashflow statements, net income, amortization and depreciation
2. Price data
3. Estimates data 
