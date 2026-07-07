# 2026-06-20下午至晚上，在 gemini和deepseek下修改数据源datasource.py与画图的逻辑，原来逻辑思路不清
from datetime import datetime, timedelta,date
from enum import Enum
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
from dataSource import get_kline_data,Ktype
import time
import code2name
    
TDX_PATH="C:/ZhaoShang"   #通达信安装目录，读取其中K线数据文件 --如：sh600036.day 

def insertDizhi(x):
    list=['亥','子','丑','寅','卯','辰','巳','午','未','申','酉','戌']
    return list[x]

def  insertDizhiMonth(x):
    list1=['丑','寅','卯','辰','巳','午','未','申','酉','戌','亥','子']
    return list1[x-1]

def calc_date_range(base_date, kline_type=Ktype.DAILY, before=10, after=30):
    # 将字符串转为日期对象
    base = datetime.strptime(base_date, "%Y-%m-%d").date()
    
    # 🌟 修改点：改用枚举类进行安全对比
    if kline_type == Ktype.DAILY:
        start = base - timedelta(days=before)
        end = base + timedelta(days=after)
    
    elif kline_type == Ktype.WEEKLY:
        start = base - timedelta(weeks=before)
        end = base + timedelta(weeks=after)
    
    elif kline_type == Ktype.MONTHLY:
        start = base - relativedelta(months=before)
        end = base + relativedelta(months=after)
    
    else:
        raise ValueError(f"不支持的K线类型: {kline_type}")
    
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

# 根据数据绘制K线图
def plot_kline(df, stock_code, kline_type: Ktype, base_date):
    # kline_name = "日K" if kline_type == Ktype.DAILY else "月K"
    kline_name = kline_type.value
    if df.empty: 
        print("数据为空，请补充数据或者这个股票已退市")
        return "alert.png"
    # df['date'] = pd.to_datetime(df['date'])
    # df.set_index('date', inplace=True)
    # 2. 在设为 index 之前，把【真实的日期数字】和【地支】先算出来
    if kline_type == Ktype.DAILY:
        # 提取真实的日数字（如 10, 11, 12...）
        # df['day'] = df['date'].dt.day  
        df['day'] = df.index.day  
        # 计算地支形成新列
        origin = pd.to_datetime('1990-12-19')
        # from_days = (df['date'] - origin).dt.days
        from_days = (df.index - origin).days
        df['from_days'] = (from_days - 5) % 12
        dizhi = df['from_days'].apply(insertDizhi)
    if kline_type == Ktype.MONTHLY:
        # 月K线逻辑
        # df['day'] = df['date'].dt.month
        df['day'] = df.index.month
        dizhi = df['day'].astype(int).apply(insertDizhiMonth)
    if kline_type == Ktype.WEEKLY:
        # 周K线逻辑，只显示周K线的月份
        df['day'] = df.index.month
        dizhi = [''] * len(df)  # 空字符串，不显示地支
    #预测日期标注在K线图上
    markday=pd.to_datetime(base_date)
    if markday in df.index:
        markpos= df.loc[markday, 'high']
    else:
        next_date = df.index[df.index > markday]
        if not next_date.empty:
            markpos= df.loc[next_date[0], 'high'] # Ret
            markday=next_date[0]
    print(markday,markpos)
    stock_name=code2name.findname_stock(stock_code) 
    #计算地支位置的比率
    maxhigh=df['high'].max()
    minlow=df['low'].min()
    amp=(maxhigh-minlow)/minlow
    posDizhi=1-amp/12    
    posDay=posDizhi-amp/12
    # 创建K线图
    fig = go.Figure(
        data=[
            go.Candlestick(
                # x=df['date'],
                x=df.index,  # 从索引取数据 
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='K线',
                increasing_line_color= 'red', decreasing_line_color= 'green',
                increasing_fillcolor='red', decreasing_fillcolor='green')
        ]
    )                            
    fig.add_trace(go.Scatter(x=df.index,y=df.low*posDizhi,mode="text",name="地支",text=dizhi,textfont=dict(size=10,color="black"))
                 )
    fig.add_trace(go.Scatter(x=df.index,y=df.low*posDay,mode="text",name="日期",text=df['day'],textfont=dict(size=10,color="blue"))
                  )
    fig.add_annotation(x=markday, y=markpos,xref='x',yref='y', text="", 
                       xanchor='right',yanchor='bottom',showarrow=True, arrowhead=1 , arrowsize=1, arrowwidth=2
                     )
    if kline_type=="日K":
        full_date_range = pd.date_range(start=df.index.min(), end=df.index.max())
        # 找出在完整日历中存在，但在你交易日数据中【不存在】的日期（即周末和长假）
        missing_dates = full_date_range.difference(pd.to_datetime(df.index))
        # 将这些缺失日期转换为 Plotly 认识的字符串格式
        vacation_list = [d.strftime('%Y-%m-%d') for d in missing_dates]
        fig.update_xaxes(
            type='date', # 保持时间轴属性，标签会自动变聪明
            rangebreaks=[
                {'values': vacation_list} # 降维打击：直接把所有非交易日全挖掉
        ])
    # 设置标题
    fig.update_layout(
        title={
            'text': f"{stock_code}{stock_name}-{kline_name}线     起卦时间: {base_date}",
            'x': 0.2, 'y': 0.99, 'xanchor': 'left', 'font_size': 12,'font_color': 'black'
        },
        showlegend=False , # 只有一个数据系列，不显示图例
        xaxis_rangeslider_visible=False, plot_bgcolor='white',  paper_bgcolor= 'white',
        width=400,height=300,
        xaxis = dict( showgrid = True, showticklabels = True,gridcolor='lightgrey' ),
        yaxis = dict( showgrid = True, showticklabels = True,gridcolor='lightgrey', ),
        margin=dict(l=20, r=10, t=10, b=10)
    )

    fig.write_html(f"{stock_code}_{base_date}{kline_name}.html")
    fig.write_image("temp100.jpg")
    # return f"{stock_code}_{kline_name}.html"
    return "temp100.jpg"
     
def drawKline(stockCode,base_date,kline_type=Ktype.DAILY,before=10,after=30,source="tdx"):
    start,end=calc_date_range(base_date, kline_type,before,after)
    df=get_kline_data(stockCode,start,end,kline_type,source)
    print(df.head(5))
    print(df.dtypes)
    img=plot_kline(df, stockCode, kline_type, base_date)
    return img


if  __name__=='__main__':
    
    stockCode="600362"
    base_date = '2026-06-01'  
    start2, end2 = calc_date_range(base_date, Ktype.DAILY, before=3, after=30)
    # start_time = time.time()
    # df2=get_kline_data(stockCode,start2,end2,Ktype.DAILY,source="tdx")
    # end_time = time.time()
    # # 计算耗时（秒）
    # elapsed_time = end_time - start_time
    # print(f"网络读取耗时: {elapsed_time * 1000:.2f} 毫秒")
    # print(df2.head(5))
    # print(df2.dtypes)
    drawKline(stockCode,base_date,kline_type=Ktype.DAILY,before=5,after=30,source="yfinance")
    


   
