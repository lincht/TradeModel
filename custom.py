import requests
import json
from robobrowser import RoboBrowser
import urllib.parse
from time import strftime, sleep
import calendar
import shutil
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_code():

    url = 'https://portal.sw.nat.gov.tw/APGA/GoodsSearch_toByCode'

    resp = requests.post(url + '2', verify = False)
    data = json.loads(resp.text)

    twos = []
    fours = []
    sixs = []
    eights = []
    elevens = []
    counter = 0

    for i in range(len(data['listBy2'])):
        twos.append(data['listBy2'][i]['cnyChinese'])

    for elementOf2 in twos:
        print(elementOf2)
        form4 = {'code2':elementOf2}
        resp4 = requests.post(url + '4', data = form4, verify = False)
        data4 = json.loads(resp4.text)
        
        for j in range(len(data4['listBy4'])):
            elementOf4 = data4['listBy4'][j]['cnyChinese']
            print(elementOf4)
            fours.append(elementOf4)
            
            form6 = {'code2':elementOf2, 'code4':elementOf4}
            resp6 = requests.post(url + '6', data = form6, verify = False)
            data6 = json.loads(resp6.text)
            
            for k in range(len(data6['listBy6'])):
                elementOf6 = data6['listBy6'][k]['cnyChinese']
                print(elementOf6)
                sixs.append(elementOf6)
                
                form8 = {'code2':elementOf2, 'code4':elementOf4, 'code6':elementOf6}
                resp8 = requests.post(url + '8', data = form8, verify = False)
                data8 = json.loads(resp8.text)
                
                for l in range(len(data8['listBy8'])):
                    elementOf8 = data8['listBy8'][l]['cnyChinese']
                    print(elementOf8)
                    eights.append(elementOf8)
                    
                    form11 = {'code2':elementOf2, 'code4':elementOf4, 'code6':elementOf6, 'code8':elementOf8}
                    resp11 = requests.post(url + '11', data = form11, verify = False)
                    data11 = json.loads(resp11.text)
                    
                    for m in range(len(data11['listBy11'])):
                        elementOf11 = data11['listBy11'][m]['cnyChinese']
                        print(elementOf11)
                        counter += 1
                        print('###### Writing code number %s' % (counter) + ' ######')
                        elevens.append(elementOf11)
    
    for collection in ['twos', 'fours', 'sixs', 'eights', 'elevens']:
        file = open(collection + '.txt', encoding = 'utf-8', mode = 'w')
        for x in eval(collection):
            file.write(x + '\n')
        file.close()
    
    file2 = open('elevens_list.txt', encoding = 'utf-8', mode = 'w')
    file2.write(str(elevens))
    file2.close()
    
    return(elevens)

url = 'https://portal.sw.nat.gov.tw/APGA/GA03_LIST?'

def get_custom(year, month):
    
    with open('elevens_list_noname.txt', encoding = 'utf-8', mode = 'r') as file:
        elevens = eval(file.read())

    filename = str(year + 1911) + '-' + str(month).zfill(2) + '.txt'
    with open(filename, encoding = 'utf-8', mode = 'w') as output:
        header = '國家|貨品分類|中文貨名|英文貨品|數量|數量單位|重量|重量單位|價值\n'
        output.write(header)
    
        for good in range(0, len(elevens) // 250 * 250 - 250 + 1, 250):
            goodsGroup = ','.join(elevens[good : good + 250])
        
            payload = [('minYear', '92'),
                       ('maxYear', '105'),
                       ('maxMonth', '6'),
                       ('minMonth', '1'),
                       ('maxYearByYear', '104'),
                       # 3: 進口總值(含復進口), 6: 出口總值(含復出口)
                       ('searchInfo.TypePort', '6'),
                       # 資料週期：0: 按月, 1: 按年
                       ('searchInfo.TypeTime', '0'),
                       # Year range: 92-105
                       ('searchInfo.StartYear', str(year)),
                       ('searchInfo.StartMonth', str(month)),
                       ('searchInfo.EndMonth', str(month)),
                       # 11碼稅則
                       ('searchInfo.goodsType', '11'),
                       ('searchInfo.goodsCodeGroup', goodsGroup),
                       # 請點選國家地區: 全部國家
                       ('searchInfo.CountryName', '請點選國家地區'),
                       # rbMoney1: 新臺幣, rbMoney2: 美元
                       ('searchInfo.Type', 'rbMoney2'),
                       # rbByGood: 按貨品別排列, rbByCountry: 按國家別
                       ('searchInfo.GroupType', 'rbByCountry'),
                       ('Search', '開始查詢')]
                   
            while True:
                try:
                    browser = RoboBrowser()
                    browser.open(url + urllib.parse.urlencode(payload), verify = False)
                    if browser.response.status_code == 200:
                        break
                except:
                    print('An error has occurred. Retrying.')
                    print(browser.response.text)
                    sleep(60)
        
            dataListNumber = 'dataList_' + str(month)
            table = browser.find_all('table', {'id':dataListNumber})
            tds = []
            for table_element in table:
                rows = table_element.find_all('tr')
                for row in rows:
                    td = row.find_all('td')
                    tds.append(td)
                
            data = ''
            for index in range(1, len(tds)):
                row_data = tds[index]
                if row_data[1].text == '合計':
                    continue
                for data_index in range(8):
                    data += row_data[data_index].text + '|'
                data += row_data[8].text + '\n'

            output.write(data)
            terminal_size = shutil.get_terminal_size()[0]
            print('Data for',
                  goodsGroup[0:10] + '-' +
                  goodsGroup[(len(goodsGroup) - 10):len(goodsGroup)],
                  calendar.month_name[month] + ', %s' % (year + 1911),
                  'written on', strftime("%Y-%m-%d %H:%M:%S"))
    
        goodsGroup2 = ','.join(elevens[len(elevens) // 250 * 250 : len(elevens)])

        payload = [('minYear', '92'),
                   ('maxYear', '105'),
                   ('maxMonth', '6'),
                   ('minMonth', '1'),
                   ('maxYearByYear', '104'),
                   # 3: 進口總值(含復進口), 6: 出口總值(含復出口)
                   ('searchInfo.TypePort', '6'),
                   # 資料週期：0: 按月, 1: 按年
                   ('searchInfo.TypeTime', '0'),
                   # Year range: 92-105
                   ('searchInfo.StartYear', str(year)),
                   ('searchInfo.StartMonth', str(month)),
                   ('searchInfo.EndMonth', str(month)),
                   # 11碼稅則
                   ('searchInfo.goodsType', '11'),
                   ('searchInfo.goodsCodeGroup', goodsGroup2),
                   # 請點選國家地區: 全部國家
                   ('searchInfo.CountryName', '請點選國家地區'),
                   # rbMoney1: 新臺幣, rbMoney2: 美元
                   ('searchInfo.Type', 'rbMoney2'),
                   # rbByGood: 按貨品別排列, rbByCountry: 按國家別
                   ('searchInfo.GroupType', 'rbByCountry'),
                   ('Search', '開始查詢')]
                   
        while True:
            try:
                browser = RoboBrowser()
                browser.open(url + urllib.parse.urlencode(payload), verify = False)
                if browser.response.status_code == 200:
                    break
            except:
                print('An error has occurred. Retrying.')
                print(browser.response.text)
                sleep(60)

        dataListNumber = 'dataList_' + str(month)
        table = browser.find_all('table', {'id':dataListNumber})
        tds = []
        for table_element in table:
            rows = table_element.find_all('tr')
            for row in rows:
                td = row.find_all('td')
                tds.append(td)
            
        data = ''
        for index in range(1, len(tds)):
            row_data = tds[index]
            if row_data[1].text == '合計':
                continue
            for data_index in range(8):
                data += row_data[data_index].text + '|'
            if index != len(tds) - 1:
                data += row_data[8].text + '\n'
            else:
                data += row_data[8].text

        output.write(data)
        print('Data for',
              goodsGroup2[0:10] + '-' +
              goodsGroup2[(len(goodsGroup2) - 10):len(goodsGroup2)],
              calendar.month_name[month] + ', %s' % (year + 1911),
              'written on', strftime("%Y-%m-%d %H:%M:%S"))
    
    print('=' * terminal_size +
    calendar.month_name[month] + ', %s' % (year + 1911),
    'data successfully downloaded on', strftime("%Y-%m-%d %H:%M:%S") + '\n' +
    '=' * terminal_size + '\n')
    return()

def get_batch_data():
    for month in range(5, 7):
        get_custom(105, month)
    for year in range(92, 105):
        for month in range(1, 13):
            get_custom(year, month)
    return()