import urllib.parse
import requests
import json
import pandas as pd
from time import strftime, sleep
import datetime
import calendar
import os.path
import secret

def check_availability(period, freq='A'):
    """
    Query data availability for the specified year.
    Return a list of dicts, each representing one available dataset.
    
    Period input:
    YYYY for annual data ('A') or YYYYMM for monthly data ('M')
    """
    url = 'http://comtrade.un.org/api//refs/da/bulk'
    payload = {'r': 'all',
               'freq': freq,
               'ps': str(period),
               'px': 'HS',
               'type': 'C',
               'token': secret.auth_code
    }
    r = requests.get(url, urllib.parse.urlencode(payload))
    return r.json()

def download_bulk(period=datetime.datetime.now().year - 1, freq='A', stream=True):
    """Return a zip file containing exactly one csv file."""
    url = 'http://comtrade.un.org/api/get/bulk/C/{}/{}/ALL/HS?token={}'.format(freq, period, secret.auth_code)
    dest = '//172.26.1.102/dstore/uncomtrade/monthly/'
    filename = dest + str(period) + '.zip'
    col_ind = { 6: 'Trade Flow Code',
                8: 'Reporter Code',
               11: 'Partner Code',
               14: 'Commodity Code',
               16: 'Qty Unit Code',
               18: 'Qty',
               19: 'Netweight (kg)',
               20: 'Trade Value (US$)'
    }
    
    # def write_stream_data(resp, filename=filename, reduce=reduce):
        # if reduce == True:
            # cols = list(col_ind.keys())
        # else:
            # cols = None
            
        # counter = 0
        # for lines in resp.iter_lines(chunk_size=100 * 1024,
                                     # decode_unicode='utf-8'):
            # if counter == 0:
                # Create file and write with headers
                # df = pd.read_csv(lines, usecols=cols, header=0)
                # df.to_csv(filename, index=False, encoding='utf-8')
                # counter += 1
            # else:
                # Append to the existing csv with no header
                # df = pd.read_csv(lines, usecols=cols, header=None)
                # with open(filename, encoding='utf-8', mode='a') as file:
                    # df.to_csv(file, index=False, header=False)
        
    if stream == False:
        r = requests.get(url)
        with open(filename, encoding='utf-8', mode='w', newline='') as file:
            file.write(r.text)
    else:
        r = requests.get(url, stream=True)
        with open(filename, mode='wb') as file:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

    size = os.path.getsize(filename) / 1024 ** 2
    print('Successfully downloaded data for {} ({} MB).'.format(str(period), str(size)))
    return

def download_monthly(year):
    for m in range(1, 13):
        period = str(year) + str(m).zfill(2)
        download_bulk(period, freq='M', stream=True)

reporters = pd.read_csv('//172.26.1.102/dstore/uncomtrade/reporter.csv')
asean = ['Singapore', 'Malaysia', 'Indonesia', 'Brunei Darussalam',
         'Lao People\'s Dem. Rep.', 'Viet Nam', 'Thailand', 'Myanmar',
         'Cambodia', 'Philippines']
south = asean + ['India', 'Sri Lanka', 'Bangladesh', 'Nepal', 'Bhutan', 'Pakistan',
                 'Australia', 'New Zealand']
asean_code = reporters[reporters['text'].isin(asean)]['id'].values
south_code = reporters[reporters['text'].isin(south)]['id'].values

def get_asean_data(partner='490'):
    batch = [south_code[0:5], south_code[5:10], south_code[10:15], south_code[15:18]]
    counter = 1
    for i in range(4):
        url = 'http://comtrade.un.org/api/get?max=50000&type=C&freq=A&px=HS&ps=all&\
r={}&p={}&rg=1&cc=TOTAL&fmt=csv'.format('%2C'.join(batch[i]), partner)
        filename = str(counter) + '.csv'
        r = requests.get(url)
        with open(filename, encoding='utf-8', mode='w', newline='') as file:
            file.write(r.text)
        counter += 1
        sleep(1) 
    
# Entire classification-years may be downloaded.
# Reporter-classification-years may be accessed as well.

# Rate limit: none
# Usage limit: 1000 requests per hour
# (per authorization code or IP address if no authorization code is used).

def get_reporters():
    
    url = 'http://comtrade.un.org/data/cache/reporterAreas.json'
    resp = requests.get(url)
    parsed_json = json.loads(resp.text)
    reporter_dict = parsed_json['results']
    reporter_df = pd.DataFrame(reporter_dict)
    reporter_array = reporter_df['id'].values
    reporter_list = [c for c in reporter_array if c != 'all']
	
    d = {reporter_dict[i]['id']: reporter_dict[i]['text'] for i in range(1, len(reporter_dict))}
    return([reporter_list, d])

def get_partners():
    
    url = 'http://comtrade.un.org/data/cache/partnerAreas.json'
    resp = requests.get(url)
    parsed_json = json.loads(resp.text)
    partner_dict = parsed_json['results']
    partner_df = pd.DataFrame(partner_dict)
    partner_array = partner_df['id'].values
    partner_list = [c for c in partner_array if c != 'all' and c != '0']
    
    d = {partner_dict[i]['id']: partner_dict[i]['text'] for i in range(1, len(partner_dict))}
    return([partner_list, d])

reporter_list = get_reporters()[0]
reporter_dict =  get_reporters()[1]
partner_list = get_partners()[0]
partner_dict =  get_partners()[1]
url = 'http://comtrade.un.org/api/get?'


def get_taiwan(year, month):
    """
    Retrieve import data of all reporting countries where Taiwan is
    partner country.
    One file per month, loop over all reporting countries.
    """
    
    filename = str(year) + '-' + str(month).zfill(2) + '.csv'
    file = open(filename, encoding = 'utf-8', mode = 'w', newline = '')
    
    # Iteration part
    counter = 0
    for i in range(0, len(reporter_list) // 5 * 5 - 5 + 1, 5):
        country_group = ','.join(reporter_list[i : i + 5])
        payload = {'max': 50000,
                   'type': 'C',
                   'freq': 'M',
                   'px': 'HS',
                   'ps': str(year) + str(month).zfill(2),
                   'r': country_group,
                   'p': '490',
                   'rg': '1',
                   'cc': 'AG6',
                   'fmt': 'csv'
        }
        while True:
            try:
                resp = requests.get(url + urllib.parse.urlencode(payload))
                if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                    break
            except:
                sleep(1)
            else:
                if resp.text == '{"Message":"An error has occurred."}':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(600)
                if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(5)
        if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
            print('No data matches for ' + country_group + '.')
            sleep(37)
            continue
        data = resp.text
        if counter != 0:
            with_header = data.split(sep = '\r\n')
            header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
            data = '\r\n'.join(header_removed)
        file.write(data)
        print('Data for ' + country_group + ' written on ' + 
            strftime("%Y-%m-%d %H:%M:%S") + '.')
        counter += 1
        sleep(37)
    
    # Last iteration
    country_group = ','.join(reporter_list[len(reporter_list) // 5 * 5 : len(reporter_list)])
    payload = {'max': 50000,
               'type': 'C',
               'freq': 'M',
               'px': 'HS',
               'ps': str(year) + str(month).zfill(2),
               'r': country_group,
               'p': '490',
               'rg': '1',
               'cc': 'AG6',
               'fmt': 'csv'
    }
    while True:
        try:
            resp = requests.get(url + urllib.parse.urlencode(payload))
            if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                break
        except:
            sleep(1)
        else:
            if resp.text == '{"Message":"An error has occurred."}':
                print('An error has occurred with message:\n' + resp.text)
                sleep(600)
            if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                print('An error has occurred with message:\n' + resp.text)
                sleep(5)
    if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
        print('No data matches for ' + country_group + '.')
        return()
    data = resp.text
    if counter != 0:
        with_header = data.split(sep = '\r\n')
        header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
        data = '\r\n'.join(header_removed)
    file.write(data)
    print('Data for ' + country_group + ' written on ' + 
        strftime("%Y-%m-%d %H:%M:%S") + '.')
    
    print('\nData for ' + calendar.month_name[month] + ', ' + str(year) +
        ' written on ' + strftime("%Y-%m-%d %H:%M:%S") + '.\n')
    file.close()
    return()

def get_taiwan_all():
    for month in range(6, 13):
        get_taiwan(2015, month)
    for month in range(1, 7):
        get_taiwan(2016, month)
    return()


def get_taiwan_annual(year):
    """
    Retrieve import data of all reporting countries where Taiwan is
    partner country.
    Loop over all reporting countries.
    """

    filename = str(year) + '.csv'
    file = open(filename, encoding = 'utf-8', mode = 'w', newline = '')
    
    # Iteration part
    counter = 0
    for i in reporter_list:
        # country_group = ','.join(reporter_list[i : i + 5])
        payload = {'max': 50000,
                   'type': 'C',
                   'freq': 'A',
                   'px': 'HS',
                   'ps': str(year),
                   'r': str(i),
                   'p': '490',
                   'rg': '1',
                   'cc': 'AG6',
                   'fmt': 'csv'
        }
        while True:
            try:
                resp = requests.get(url + urllib.parse.urlencode(payload))
                if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                    break
            except:
                sleep(1)
            else:
                if resp.text == '{"Message":"An error has occurred."}':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(37)
                    continue
                if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(5)
        if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
            print('No data matches for ' + str(i) + '.')
            sleep(37)
            continue
        data = resp.text
        if counter != 0:
            with_header = data.split(sep = '\r\n')
            header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
            data = '\r\n'.join(header_removed)
        file.write(data)
        print('Data for ' + str(i) + ' written on ' + 
            strftime("%Y-%m-%d %H:%M:%S") + '.')
        counter += 1
        sleep(37)
    
    # Last iteration
    # country_group = ','.join(reporter_list[len(reporter_list) // 5 * 5 : len(reporter_list)])
    # payload = {'max': 50000,
               # 'type': 'C',
               # 'freq': 'A',
               # 'px': 'HS',
               # 'ps': str(year),
               # 'r': country_group,
               # 'p': '490',
               # 'rg': '1',
               # 'cc': 'AG6',
               # 'fmt': 'csv'
    # }
    # while True:
        # try:
            # resp = requests.get(url + urllib.parse.urlencode(payload))
            # if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                # break
        # except:
            # sleep(1)
        # else:
            # if resp.text == '{"Message":"An error has occurred."}':
                # print('An error has occurred with message:\n' + resp.text)
                # sleep(600)
            # if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                # print('An error has occurred with message:\n' + resp.text)
                # sleep(5)
    # if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
        # print('No data matches for ' + country_group + '.')
        # return()
    # data = resp.text
    # if counter != 0:
        # with_header = data.split(sep = '\r\n')
        # header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
        # data = '\r\n'.join(header_removed)
    # file.write(data)
    # print('Data for ' + country_group + ' written on ' + 
        # strftime("%Y-%m-%d %H:%M:%S") + '.')
    
    print('\nData for ' + calendar.month_name[month] + ', ' + str(year) +
        ' written on ' + strftime("%Y-%m-%d %H:%M:%S") + '.\n')
    file.close()
    return()

def get_taiwan_annual_all():
    for year in [2016]:
        get_taiwan(year)
    return()


def get_import(reporter_id):
    """
    Retrieve import data of one single reporting country from all partner countries.
    Loop over all time periods and all partner countries.
    """
    
    filename = reporter_dict[reporter_id].replace(' ', '_').lower() + '.csv'
    file = open(filename, encoding = 'utf-8', mode = 'w', newline = '')
    periods = [str(year) + str(month).zfill(2) for year in range(2010, 2016) for month in range(1, 13)]
    periods.extend(['2016' + str(month).zfill(2) for month in range(1, 5)])
	
    # Outer iteration part
    counter = 0
    for i in range(0, len(periods) // 3 * 3 - 3 + 1, 3):
        period_group = ','.join(periods[i : i + 3])
        # Inner iteration part, of outer iteration part
        for j in range(0, len(partner_list) // 5 * 5 - 5 + 1, 5):
            partner_group = ','.join(partner_list[j : j + 5])
            payload = {'max': 50000,
                       'type': 'C',
                       'freq': 'M',
                       'px': 'HS',
                       'ps': period_group,
                       'r': reporter_id,
                       'p': partner_group,
                       'rg': '1',
                       'cc': 'AG6',
                       'fmt': 'csv'
            }
            while True:
                try:
                    resp = requests.get(url + urllib.parse.urlencode(payload))
                    if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                        break
                except:
                    sleep(1)
                else:
                    if resp.text == '{"Message":"An error has occurred."}':
                        print('An error has occurred with message:\n' + resp.text)
                        sleep(600)
                    if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                        print('An error has occurred with message:\n' + resp.text)
                        sleep(5)
            if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
                print('No data matches for ' + period_group + ', partners ' + partner_group + '.')
                sleep(37)
                continue
            data = resp.text
            if counter != 0:
                with_header = data.split(sep = '\r\n')
                header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
                data = '\r\n'.join(header_removed)
            file.write(data)
            print('Data for ' + period_group + ', partners ' + partner_group + ' written on ' + 
                strftime("%Y-%m-%d %H:%M:%S") + '.')
            counter += 1
            sleep(37)

        # Last inner iteration, of outer iteration part
        partner_group = ','.join(partner_list[len(partner_list) // 5 * 5 : len(partner_list)])
        payload = {'max': 50000,
                   'type': 'C',
                   'freq': 'M',
                   'px': 'HS',
                   'ps': period_group,
                   'r': reporter_id,
                   'p': partner_group,
                   'rg': '1',
                   'cc': 'AG6',
                   'fmt': 'csv'
        }
        while True:
            try:
                resp = requests.get(url + urllib.parse.urlencode(payload))
                if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                    break
            except:
                sleep(1)
            else:
                if resp.text == '{"Message":"An error has occurred."}':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(600)
                if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(5)
        if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
            print('No data matches for ' + period_group + ', partners ' + partner_group + '.')
            return()
        data = resp.text
        if counter != 0:
            with_header = data.split(sep = '\r\n')
            header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
            data = '\r\n'.join(header_removed)
        file.write(data)
        print('Data for ' + period_group + ', partners ' + partner_group + ' written on ' + 
            strftime("%Y-%m-%d %H:%M:%S") + '.')
        
        print('Data for ' + period_group + ' for ALL PARTNERS written on ' +
            strftime("%Y-%m-%d %H:%M:%S") + '.')

    # Last outer iteration
    period_group = ','.join(periods[len(periods) // 3 * 3 : len(periods)])
    # Inner iteration part, of last outer iteration
    for j in range(0, len(partner_list) // 5 * 5 - 5 + 1, 5):
        partner_group = ','.join(partner_list[j : j + 5])
        payload = {'max': 50000,
                   'type': 'C',
                   'freq': 'M',
                   'px': 'HS',
                   'ps': period_group,
                   'r': reporter_id,
                   'p': partner_group,
                   'rg': '1',
                   'cc': 'AG6',
                   'fmt': 'csv'
        }
        while True:
            try:
                resp = requests.get(url + urllib.parse.urlencode(payload))
                if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                    break
            except:
                sleep(1)
            else:
                if resp.text == '{"Message":"An error has occurred."}':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(600)
                if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                    print('An error has occurred with message:\n' + resp.text)
                    sleep(5)
        if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
            print('No data matches for ' + period_group + ', partners ' + partner_group + '.')
            sleep(37)
            continue
        data = resp.text
        if counter != 0:
            with_header = data.split(sep = '\r\n')
            header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
            data = '\r\n'.join(header_removed)
        file.write(data)
        print('Data for ' + period_group + ', partners ' + partner_group + ' written on ' + 
            strftime("%Y-%m-%d %H:%M:%S") + '.')
        counter += 1
        sleep(37)

    # Last inner iteration, of last outer iteration
    partner_group = ','.join(partner_list[len(partner_list) // 5 * 5 : len(partner_list)])
    payload = {'max': 50000,
               'type': 'C',
               'freq': 'M',
               'px': 'HS',
               'ps': period_group,
               'r': reporter_id,
               'p': partner_group,
               'rg': '1',
               'cc': 'AG6',
               'fmt': 'csv'
    }
    while True:
        try:
            resp = requests.get(url + urllib.parse.urlencode(payload))
            if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                break
        except:
            sleep(1)
        else:
            if resp.text == '{"Message":"An error has occurred."}':
                print('An error has occurred with message:\n' + resp.text)
                sleep(600)
            if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                print('An error has occurred with message:\n' + resp.text)
                sleep(5)
    if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
        print('No data matches for ' + period_group + ', partners ' + partner_group + '.')
        return()
    data = resp.text
    if counter != 0:
        with_header = data.split(sep = '\r\n')
        header_removed = [with_header[x] for x in range(len(with_header)) if x != 0]
        data = '\r\n'.join(header_removed)
    file.write(data)
    print('Data for ' + period_group + ', partners ' + partner_group + ' written on ' + 
        strftime("%Y-%m-%d %H:%M:%S") + '.')
    
    print('Data for ' + period_group + ' for ALL PARTNERS written on ' + 
        strftime("%Y-%m-%d %H:%M:%S") + '.')
    
    print('\nData for ' + reporter_dict[reporter_id].replace(' ', '_').lower() +
        ' written on ' + strftime("%Y-%m-%d %H:%M:%S") + '.\n')
    file.close()
    return()

def find_key(input_dict, value):
    return(next((k for k, v in input_dict.items() if v == value), None))

def get_import_selected():
    for reporter_id in [find_key(reporter_dict, x) for x in ['China', 'Indonesia', 'India', 'Viet Nam', 'Turkey', 'USA']]:
        get_import(reporter_id)

def get_import_all():
    for reporter_id in reporter_dict:
        get_import(reporter_id)


def get_import_from_world(reporter_id):
    """
    Retrieve import data of one single reporting country from the world.
    Loop over 2014, 2015 (annually) and all partner countries.
    """
    filename = reporter_dict[reporter_id].replace(' ', '_').lower() + '.csv'
    if os.path.isfile(filename) == True:
        return()
    payload = {'max': 50000,
               'type': 'C',
               'freq': 'A',
               'px': 'HS',
               'ps': '2012,2013',
               'r': reporter_id,
               'p': '0',
               'rg': '1',
               'cc': 'AG6',
               'fmt': 'csv'
    }
    while True:
        try:
            resp = requests.get(url + urllib.parse.urlencode(payload))
            if resp.text != '{"Message":"An error has occurred."}' and resp.text != 'RATE LIMIT: You must wait 1 seconds.':
                break
        except:
            sleep(1)
        else:
            if resp.text == '{"Message":"An error has occurred."}':
                print('An error has occurred with message:\n' + resp.text)
                sleep(600)
            if resp.text == 'RATE LIMIT: You must wait 1 seconds.':
                print('An error has occurred with message:\n' + resp.text)
                sleep(5)
                
    if resp.text.split(sep = '\r\n')[1] == 'No data matches your query or your query is too complex. Request JSON or XML format for more information.,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,':
        print('No data matches for ' + reporter_dict[reporter_id].replace(' ', '_').lower())
        sleep(37)
        return()
    data = resp.text
    filename = reporter_dict[reporter_id].replace(' ', '_').lower() + '.csv'
    with open(filename, encoding = 'utf-8', mode = 'w', newline = '') as file:
        file.write(data)
    print('\nData for ' + reporter_dict[reporter_id].replace(' ', '_').lower() +
        ' written on ' + strftime("%Y-%m-%d %H:%M:%S") + '.\n')
    return()

def get_import_from_world_all():
    for reporter_id in reporter_dict:
        get_import_from_world(reporter_id)