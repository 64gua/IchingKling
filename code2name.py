import pandas as pd
import re

def findname_stock(codestr):  #csv 文件中有股票和ETF名单，包括大盘与创业板代号
    df=pd.read_csv("stock_and_etf.csv",dtype={0:"string",1:"string"})
    stocks = df.loc[df['code'] == codestr, 'name']
    if  stocks.empty:
        name="NULL"
    else:
        name=stocks.values[0] 
    return name

def findcode_stock(namestr):
    df=pd.read_csv("stock_and_etf.csv",dtype={0:"string",1:"string"})
    stock_code = df.loc[df['name'].str.contains(namestr), 'code']
    if  stock_code.empty:
        code="NULL"
    else:
        code=stock_code.values[0]
    return code
    
def extractStockName(contents):
    code="NULL"
    name="NULL"
    re2=r'sh000001|000001.XSHG|大盘|上证|深成指|综指|沪深|沪市|沪指|股市'
    stockFind=re.findall(re2,contents)
    if stockFind:
        code="sh000001"
        name="上证指数"
        return code,name
    re0=r'创业板指|399006'
    stockFind=re.findall(re0, contents)
    if stockFind:
        code="399006"
        name="创业板"
        return code, name
    re1=r'中小板|399005'
    stockFind=re.findall(re1, contents)
    if stockFind:
        code="399005"
        name="中小板"
        return code, name
    if contents=="增删" or contents== "热点"  or contents== "高岛" or contents== "财运":
        code=contents
        name="人事"
        return code, name  
    re3=r'(?<![a-zA-Z])\d{6}(?![a-zA-Z])(?!\.)'
    stockFind=re.findall(re3,contents)
    #cleaned_stock_codes = [code for code in stock_codes if not any(re.search(code, link) for link in re.findall(r'img\d+\.jpg', sample_text))]
    if stockFind:
        re_img=r'images.+jpg|images.+.jpeg|images.+png'
        images=re.findall(re_img,contents)
        if len(images)>0:
            for imglink in images:
                if stockFind[0] in imglink:
                    return "NULL","NULL"
        code= stockFind[0]
        name=findname_stock(code)
        return code, name
    stock_df=pd.read_csv("stock_and_etf.csv",dtype={0:"string",1:"string"})
    for stock_name in stock_df['name']:
        stock_name1=stock_name.replace("ST","").replace("*","")
        if  contents.find(stock_name1)>-1:
            #print("股票名字为:"+stock_name)
            stock_code=findcode_stock(stock_name1)
            return stock_code,stock_name
    return code,name

if  __name__=='__main__':
    input_namestr="思源电气"
    input_codestr="600036"
    code=findcode_stock(namestr=input_namestr)
    name=findname_stock(input_codestr)
    print(code)
    print(name)
