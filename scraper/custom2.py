import datetime
import requests
import urllib.parse
import pandas as pd
from time import strftime, sleep
import calendar
import shutil
from requests.packages.urllib3.exceptions import InsecureRequestWarning

"""
Note: If you're using R, the recommended approach to read the downloaded data
is as follows:

# R code:    
requre(readr)
df <- read_delim(path, delim = '\t', col_types = 'ccccdcdcd')    
"""

curr_time = datetime.datetime.now()
curr_year = curr_time.year - 1911
prev_month = curr_time.month - 1
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_custom_data(year=curr_year, month=prev_month, io='export',
                    currency='usd'):
    """
    Return monthly custom data.
    
    Parameters
    ----------
    year :  int, default current (ROC calendar) year.
    month : int, default one month prior to current month.
    io: {'import', 'export'}, default 'export'.
    currency : {'usd', 'ntd'}, default 'usd'.
    
    """
    
    # argument checking
    if year > curr_year or year < 92:
        raise ValueError('Invalid year. Valid years are 92 - %d.' % curr_year)
    if month not in range(1, 13):
        raise ValueError('Invalid month. Valid months are 1 - 12.')
    if io not in ['import', 'export']:
        raise ValueError('Invalid io. Must be either "import" or "export".')
    if currency not in ['usd', 'ntd']:
        raise ValueError('Invalid currency. Must be either "usd" or "ntd".')
    
    # load list of commodity codes
    with open('elevens_list_noname.txt', encoding='utf-8', mode='r') as file:
        elevens = eval(file.read())
    
    # define some useful variables
    url = 'https://portal.sw.nat.gov.tw/APGA/GA03_LIST?'
    colnames = ['國家', '貨品分類', '中文貨名', '英文貨名', '數量', '數量單位',
    '重量', '重量單位', '價值']
    df = pd.DataFrame(columns=colnames)    
    
    def generate_payload(commodities, year=year, month=month, io=io,
                         currency=currency):
        """
        Generate payload for sending requests.
        
        Parameters
        ----------
        commodities : comma-separated str.
        
        """
        
        payload = [('minYear', '92'),
                   ('maxYear', str(curr_year)),
                   ('maxMonth', str(prev_month)),
                   ('minMonth', '1'),
                   ('maxYearByYear', str(curr_year - 1)),
                   # 3: 進口總值(含復進口), 6: 出口總值(含復出口)
                   ('searchInfo.TypePort', '6' if io == 'export' else '3'),
                   # 資料週期：0: 按月, 1: 按年
                   ('searchInfo.TypeTime', '0'),
                   # Year range: 92-105
                   ('searchInfo.StartYear', str(year)),
                   ('searchInfo.StartMonth', str(month)),
                   ('searchInfo.EndMonth', str(month)),
                   # 11碼稅則
                   ('searchInfo.goodsType', '11'),
                   ('searchInfo.goodsCodeGroup', commodities),
                   # 請點選國家地區: 全部國家
                   ('searchInfo.CountryName', '請點選國家地區'),
                   # rbMoney1: 新臺幣, rbMoney2: 美元
                   ('searchInfo.Type', 'rbMoney2' if currency == 'usd' else 'rbMoney1'),
                   # rbByGood: 按貨品別排列, rbByCountry: 按國家別
                   ('searchInfo.GroupType', 'rbByCountry'),
                   ('Search', '開始查詢')]
        return payload
    
    def get_data(payload):
        """
        Send request and save requested data as DataFrame.
        
        """
        
        while True:
            try:
                res = requests.get(url + urllib.parse.urlencode(payload), verify=False)
                if res.ok:
                    break
            except:
                print('An error has occurred with status code %d. Retrying.' % res.status_code)
                sleep(60)
        tb = pd.read_html(res.text)
        df = tb[11]
        df.columns = colnames
        df = df.query('貨品分類 != "合計"').drop(0, axis=0)
        return df
        
    def report_progress(start, end):
        """
        Print verbose progress report.
        
        """

        print('Processing data for',
              start + '-' + end,
              calendar.month_name[month] + ', %s' % (year + 1911),
              'on', strftime("%Y-%m-%d %H:%M:%S"))
        return

    # iterate over commodity codes
    for com in range(0, len(elevens) // 250 * 250 - 250 + 1, 250):
        start_ind = com
        end_ind = com + 250
        report_progress(elevens[start_ind], elevens[end_ind - 1])
        batch = ','.join(elevens[start_ind:end_ind])
        payload = generate_payload(commodities=batch)
        df = pd.concat([df, get_data(payload)], axis=0, ignore_index=True)
    last = ','.join(elevens[len(elevens) // 250 * 250 : len(elevens)])
    payload = generate_payload(commodities=last)
    df = pd.concat([df, get_data(payload)], axis=0, ignore_index=True)
    
    # write data
    if currency == 'usd':
        placeholder1 = 'us'
    else:
        placeholder1 = 'nt'
    if io == 'export':
        placeholder2 = 'rev'
    else:
        placeholder2 = 'import'
    filename = '//172.20.23.190/ds/Raw Data/MOF-{}-2003-2017-{}/\
{}-{}.tsv'.format(placeholder1, placeholder2, str(year + 1911), str(month).zfill(2))
    # filename = str(year + 1911) + '-' + str(month).zfill(2) + '.tsv'
    with open(filename, encoding='utf-8', mode='w') as output:
        df.to_csv(output, sep='\t', header=True, index=False, encoding='utf-8')
        
    terminal_size = shutil.get_terminal_size()[0]
    line = '=' * terminal_size + '\n'
    print(line + calendar.month_name[month] + ', %s' % (year + 1911),
    'data successfully downloaded on',
    strftime("%Y-%m-%d %H:%M:%S") + '\n' + line)

    return

if __name__ == '__main__':
    get_custom_data()
    