import requests
import re
from urllib.parse import quote
import json
import math
from termcolor import cprint
import time
import argparse

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0'}

total_list = []
companyName_list = []

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def chinazApi(domain):
    global companyName_list

    # 解析chinaz返回结果的json数据
    def parse_json(json_ret):
        chinazNewDomains = []
        results = json_ret['data']
        for result in results:
            companyName = result['webName']
            newDomain = result['host']
            time = result['verifyTime']
            chinazNewDomains.append((companyName, newDomain, time))     #
        chinazNewDomains = list(set(chinazNewDomains))
        return chinazNewDomains

    cprint('Load chinazApi: ', 'green')

    chinazNewDomains = []
    tempDict = {}
    tempList = []

    # 获取域名的公司名字
    url = r'http://icp.chinaz.com/{}'.format(domain)
    try:
        res = requests.get(url=url, headers=headers,verify=False,proxies=proxies)
    except Exception as e:
        print('[error] request : {}\n{}'.format(url, e.args))
        return []
    text = res.text
    companyName = re.search("var kw = '([\S]*)'", text)
    if companyName:
        companyName = companyName.group(1)
        if len(companyName) <= 4:
            print("这绝逼是个人域名"+companyName)
            return []
        for cpn in companyName_list:
            if cpn == companyName:
                print("这个公司名称已经出现过了"+cpn+"--------"+companyName)
                return []      
        companyName_list.append(companyName)
        print('公司名: {}'.format(companyName))
        companyNameUrlEncode = quote(str(companyName))
    else:
        print('没有匹配到公司名')
        return []

    # 备案反查域名
    headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
    url = 'http://icp.chinaz.com/Home/PageData'
    data = 'pageNo=1&pageSize=20&Kw=' + companyNameUrlEncode
    try:
        res = requests.post(url=url, headers=headers, proxies=proxies,data=data, allow_redirects=False, verify=False)
    except Exception as e:
        print('[error] request : {}\n{}'.format(url, e.args))
        return []

    json_ret = json.loads(res.text)
    # print(json_ret)
    if 'amount' not in json_ret.keys():
        return chinazNewDomains
    amount = json_ret['amount']
    pages = math.ceil(amount / 20)
    print('页数: {}'.format(pages))
    # 解析返回的json数据包，过滤出公司名，域名，时间
    tempList.extend(parse_json(json_ret))
    # for _ in chinazNewDomains:
    #     print(_)

    # 继续获取后面页数
    for page in range(2, pages+1):
        print('请求第{}页'.format(page))
        data = 'pageNo={}&pageSize=20&Kw='.format(page) + companyNameUrlEncode
        try:
            res = requests.post(url=url, headers=headers, data=data, allow_redirects=False, verify=False)
            json_ret = json.loads(res.text)
            tempList.extend(parse_json(json_ret))
        except Exception as e:
            print('[error] request : {}\n{}'.format(url, e.args))


    for each in tempList:
        if each[1] not in tempDict:
            tempDict[each[1]] = each
            chinazNewDomains.append(each)

    print('chinazApi去重后共计{}个顶级域名'.format(len(chinazNewDomains)))
    # for _ in chinazNewDomains:
    #     print(_)
    if len(chinazNewDomains) > 0:
        with open('result.txt','a+',encoding="utf-8",errors="ignore") as w:
            for newdomain in chinazNewDomains:
                if check_contain_chinese(newdomain[1]):
                    continue
                w.write(newdomain[1]+"\n")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", dest='file', help="目标文件")

    args = parser.parse_args()
  
    with open(args.file,'rt',encoding="utf-8",errors="ignore") as f:
        domains = f.readlines()
        num =0
        for domain in domains:
            num += 1
            print("<><><><><><><><><>第"+str(num)+"页"+"<><><><><><><><><>")
            chinazApi(domain.strip())
            time.sleep(5)

    print("end 排除了这么多家"+str(len(companyName_list)))
