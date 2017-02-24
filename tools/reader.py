# Functions for reading:
#   1. ITC 
#   2. UN
#   3. MOF company trade data
#   4. MOF customs data
#   5. Product descriptions (MOF or UN)
#   6. Country codes (MOF or UN reporter/partner)

import os
import itertools
import pandas as pd
import re
from functools import reduce
from io import StringIO

def read_itc():
    """
    Read ITC HS4 import data. Year range: 2001 to 2015.
    Variables: importing country, product code, partner (yearly value spread across columns).
    """
    path = '//172.20.23.190/ds/Raw Data/2016大數爬蟲案/data/ITC HS4/all/'
    files = pd.Series(os.listdir(path))
    # Filter for import data
    files = files[files.str.contains('_I')]
    df_map = map(lambda f: pd.read_csv(path + f, index_col=0,
                                       dtype={'Country': 'object',
                                              'Product Code': 'object',
                                              'Partner': 'object',
                                              'Value in 2001': 'float',
                                              'Value in 2002': 'float',
                                              'Value in 2003': 'float',
                                              'Value in 2004': 'float',
                                              'Value in 2005': 'float',
                                              'Value in 2006': 'float',
                                              'Value in 2007': 'float',
                                              'Value in 2008': 'float',
                                              'Value in 2009': 'float',
                                              'Value in 2010': 'float',
                                              'Value in 2011': 'float',
                                              'Value in 2012': 'float',
                                              'Value in 2013': 'float',
                                              'Value in 2014': 'float',
                                              'Value in 2015': 'float'}), files)
    df = reduce(lambda x, y: pd.concat([x, y], axis=0, ignore_index=True), df_map)
    # Remove the leading single quote (') in product code column
    df['Product Code'] = df['Product Code'].apply(lambda x: x[1:])
    # Remove HS6 rows
    df = df[df['product'].apply(len) == 4]
    return df

def read_un(start=2011, end=2015):
    """
    Read UN HS6 import data. Available year range: 2011 to 2015.
    Variables: reporter, commodity, partner, year.
    """
    def read_yearly(year):
        path = '//172.26.1.102/dstore/uncomtrade/annual_reduced/'
        df = pd.read_csv(path + str(year) + '.csv', header=0,
                         names=['flow', 'reporter', 'partner', 'commodity', 'val'],
                         dtype={'flow': int,
                                'reporter': int,
                                'partner': int,
                                'commodity': str,
                                'val': float})
        # Keep only import data (flow == 1)
        df = df[df['flow'] == 1].drop('flow', axis=1)
        # Get HS6 rows and pad 0's to have length 6
        df = df[df['commodity'].str.len() >= 5]
        df['commodity'] = df['commodity'].apply(lambda x: x.zfill(6))
        # Add year column
        df['year'] = year
        return df
    df = reduce(lambda x, y: pd.concat([x, y], axis=0, ignore_index=True),
                map(read_yearly, range(start, end + 1)))
    return df
    
def read_company_trade():
    """
    Read MOF company HS6 export and import data. Month range: 2014-01 to 2016-10.
    Variables: ban, code, country (year and month as index).
    """
    path = 'C:/Users/2093/Desktop/Data Center/03. Data/06. companies/財政部廠商進出口資料/KMG_HS6COUNTRY.csv'
    df = pd.read_csv(path, names=['ban', 'code', 'country', 'year', 'month', 'ex', 'im'], header=0,
                     dtype={'ban': str, 'code': str, 'country': str, 'year': str, 'month': str,
                            'ex': int, 'im': int})
    # Remove yearly total rows
    df = df[df['month'].notnull()]
    # Pad zeros and construct DatetimeIndex
    df['month'] = df['month'].apply(lambda x: x.zfill(2))
    df.index = pd.to_datetime(df['year'] + df['month'], format='%Y%m')
    df.index.name = 'date'
    # Drop original year and month columns
    df = df.drop(['year', 'month'], axis=1)
    return df
    
def read_customs(start='2003-01', end='2016-12'):
    """
    Read MOF customs HS10 export data. Available month range: from 2003-01.
    Variables: country, code (year and month as index).
    """
    def read_monthly(year, month):
        date = str(year) + '-' + str(month).zfill(2)
        df = pd.read_csv('//172.20.23.190/ds/Raw Data/MOF-us-2003-2017-rev/' + date + '.tsv', sep='\t',
                         usecols=['國家', '貨品分類', '價值'])
        df.columns = ['country', 'code', 'val']
        df['date'] = pd.to_datetime(date, format='%Y-%m')
        df.set_index('date', inplace=True)
        return df
        
    start = pd.to_datetime(start, format='%Y-%m')
    end = pd.to_datetime(end, format='%Y-%m')
    if (end - start).days < 0:
        raise ValueError('Start date later than end date')
    if start.year < end.year:
        dates = [(start.year, m) for m in range(start.month, 13)]
        if end.year - start.year >= 2:
            years = range(start.year + 1, end.year)
            months = range(1, 13)
            dates += list(itertools.product(years, months))
        dates += [(end.year, m) for m in range(1, end.month + 1)]
    else:
        dates = [(start.year, m) for m in range(start.month, end.month + 1)]

    # Iterate over (year, month) pairs and join results
    df_map = map(lambda x, y: read_monthly(year=x, month=y),
                 [x[0] for x in dates], [x[1] for x in dates])
    df = reduce(lambda x, y: pd.merge(left=x, right=y, how='outer', left_index=True, right_index=True),
                df_map)
    # Impute NA's
    df.fillna(0, inplace=True)
    return df

def read_product_desc(source='mof'):
    """
    Read product descriptions.
    
    Parameters
    ----------
    source : string, optional (default='mof')
        Supported sources are 'mof' for MOF and 'un' for UN.
        - If 'mof', then variables are product (HS2 to HS8), desc.
        - If 'un', then variables are product (HS2 to HS6), parent, desc.
          Note that there are six special codes: 'ALL', 'TOTAL', 'AG2', 'AG4', 'AG6', '9999AA'.
    """
    if source == 'mof':
        path = ('C:/Users/2093/Desktop/Data Center/03. Data/01. HS_code/customs/' +
        '稅則貨名檔(八碼)_最後更新時間 2017-02-07/note_8_C.txt')
        with open(path, encoding='utf-8') as f:
            txt = f.read()
        # Handle some parsing issues
        txt = re.sub(r'(\d)[ ]+', r'\1 ', txt)
        txt = re.sub(r',', '，', txt)
        txt = re.sub(r'(\D)[ ]+', r'\1', txt)
        txt = re.sub(r'HS_NONOTE', r'HS_NO NOTE', txt)
        desc = pd.read_csv(StringIO(txt), sep=' ', header=0, names=['product', 'desc'])
        return desc
    elif source == 'un':
        path = '//172.26.1.102/dstore/uncomtrade/HS_utf-8.csv'
        desc = pd.read_csv(path, header=0, names=['product', 'parent', 'desc'])
        return desc
    else:
        raise ValueError('Invalid source arg "{}"'.format(source))

def read_country_code(source='mof'):
    """
    Read country codes.
    
    Parameters
    ----------
    source : string, optional (default='mof')
        Supported sources are 'mof' for MOF, 'un_rep' for UN reporters, 'un_par' for UN partners.
        - If 'mof', then variables are code, country, region.
        - If 'un_rep' or 'un_par', then variables are code and country.
          Note that there is one special code 'all'.
    """
    if source == 'mof':
        return pd.read_csv('C:/Users/2093/Desktop/Data Center/03. Data/05. TAITRA/CRM/country.csv',
                           usecols=[0, 1, 3], header=0, names=['code', 'country', 'region']).apply(
            lambda x: x.str.strip())
    elif source == 'un_rep':
        return pd.read_csv('//172.26.1.102/dstore/uncomtrade/reporter.csv', header=0,
                           names=['code', 'country'])
    elif source == 'un_par':
        return pd.read_csv('//172.26.1.102/dstore/uncomtrade/partner.csv', header=0,
                           names=['code', 'country'])
    else:
        raise ValueError('Invalid source arg "{}"'.format(source))