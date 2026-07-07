from enum import Enum
import pandas as pd
import os,struct
from   datetime import datetime, timedelta
import requests
import json
import baostock as bs
import yfinance as yf
import urllib3
import socket
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Ktype(str, Enum):
    DAILY = "日K"
    WEEKLY = "周K"
    MONTHLY = "月K"

TDX_PATH="C:/ZhaoShang"   #通达信安装目录，读取其中K线数据文件 --如：sh600036.day 

# ==========================================
# 第一部分：四大底层驱动函数（由你之前的代码改造）,
# 注意sina只能提供2000条数据左右。akshare经常被东方财富反爬虫，此处代码排除，代码保存在data_from_akshare里； yfinance要科学上网
# ==========================================
 

def _get_from_tdx(symbol: str, start_date: str, end_date: str, kline_type: Ktype= Ktype.DAILY):
    # 你之前写的 yfinance 核心逻辑
    """
    获取指定股票在指定时间段的数据
    :param symbol: 股票代码      :param start_date: 开始日期，格式 'YYYY-MM-DD'
    :param end_date: 结束日期，格式 'YYYY-MM-DD'  
    :param tdx_path: 通达信数据路径       :return: 包含指定时间段数据的 DataFrame
    """
    if symbol.startswith('6') or symbol.startswith('5') or symbol.startswith('9') or symbol.startswith('88'):
        market = 'sh'
    if symbol.startswith('0') or symbol.startswith('3') or symbol.startswith("1"):
        market = 'sz'
    if symbol=="sh000001":
        filename="999999"
        market="sh"
    else:
        filename=symbol
    file_path = os.path.join(TDX_PATH, 'vipdoc', market, 'lday', f'{market}{filename}.day')
    
    print(file_path)
    df = read_tdx_day_data(file_path)
    if kline_type==Ktype.DAILY:   #日线
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    if kline_type==Ktype.WEEKLY:
        df=generate_weekly_kline(df,start_date,end_date)
    if kline_type==Ktype.MONTHLY:
       df=generate_monthly_kline(df,start_date,end_date)
    # print(df.head(5))
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    df.index.name = "date"
    return df

def generate_monthly_kline(df, start_date,end_date):
    #从日K线数据中生成月K线
    print("generate monthly  start ......")
    day1=datetime.strptime(start_date,"%Y-%m-%d").date()
    day2=datetime.strptime(end_date,"%Y-%m-%d").date()
    first_day=datetime(day1.year,day1.month,1)
    if day2.month==12:
        last_day=datetime(day2.year,12,31)
    else:
        last_day=datetime(day2.year,day2.month+1,1)-timedelta(days=1)
    first_day_str=first_day.strftime("%Y-%m-%d")
    last_day_str=last_day.strftime("%Y-%m-%d")
    df = df[(df['date'] >= first_day_str) & (df['date'] <= last_day_str)]
    df.set_index('date',inplace=True)
    monthly_kline=df.resample('ME').agg({
        'open':'first',
        'close':'last',
        'high':'max',
        'low':'min'
    })
    monthly_kline.reset_index(inplace=True)
    return monthly_kline

def generate_weekly_kline(df, start_date, end_date):
    # 从日K线数据中生成周K线
    print("generate weekly  start ......")

    # 1. 规整日期边界（确保把包含开始和结束日期的完整周的数据都纳入计算）
    day1 = datetime.strptime(start_date, "%Y-%m-%d").date()
    day2 = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 寻找 start_date 所在周的周一
    first_day = day1 - timedelta(days=day1.weekday())
    # 寻找 end_date 所在周的周日（为了包住周五的数据，推算到周日最保险）
    last_day = day2 + timedelta(days=(6 - day2.weekday()))

    first_day_str = first_day.strftime("%Y-%m-%d")
    last_day_str = last_day.strftime("%Y-%m-%d")

    # 2. 过滤数据
    df = df[(df["date"] >= first_day_str) & (df["date"] <= last_day_str)].copy()

    # 3. 将 date 转为 DatetimeIndex
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    # 4. 按周重采样聚合
    # 'W-FRI' 代表以周五为一周的结束点，聚合这一周内的股票表现
    # 如果你的 pandas 版本较老，可能会用到 'W'，而新版推荐精确指定 'W-FRI'
    weekly_kline = df.resample("W-FRI").agg(
        {"open": "first", "close": "last", "high": "max", "low": "min", "volume": "sum"}
    )

    # 5. 清理空数据（比如遇到国庆长假、春节长假，整周都没有交易日的情况）
    weekly_kline.dropna(subset=["open"], inplace=True)

    # 6. 还原索引结构，格式化日期
    weekly_kline.reset_index(inplace=True)
    weekly_kline["date"] = weekly_kline["date"].dt.strftime("%Y-%m-%d")

    return weekly_kline


def read_tdx_day_data(file_path):
    """
    读取通达信日线数据文件
    :param file_path: 数据文件路径
    :return: 包含数据的 DataFrame
    """
    data = []
    with open(file_path, 'rb') as f:
        while True:
            block = f.read(32)
            if not block:
                break
            # 解析数据
            (date, open_price, high, low, close, amount, volume, _) = struct.unpack('<IIIIIfII', block)
            date_str = str(date)
            date_formatted = f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}'
            data.append([date_formatted, open_price / 100, high / 100, low / 100, close / 100, amount, volume])
    columns = ['date', 'open', 'high', 'low', 'close', 'amount', 'volume']
    df = pd.DataFrame(data, columns=columns)
    df['date'] = pd.to_datetime(df['date'])
    return df


def _get_from_baostock(symbol: str, start_date: str, end_date: str, kline_type: Ktype = Ktype.DAILY):
    """使用 BaoStock 获取 A 股指定时间段的 K 线信息（已修复 VPN 卡死与异常处理）
    :param symbol: 股票代码，支持带后缀(如 '600519.SS')、纯数字(如 '600519') 或 BaoStock格式(如 'sh.600519')
    :param start_date: 开始日期，格式 'YYYY-MM-DD'
    :param end_date: 结束日期，格式 'YYYY-MM-DD'
    :param kline_type: K线类型，来自 Ktype 枚举
    :return: 包含K线数据的 pandas DataFrame
    """
    # 保存系统默认的 socket 超时时间，用于最后恢复
    default_timeout = socket.getdefaulttimeout()
    is_logged_in = False
    
    try:
        # --- 核心修复：设置 5 秒超时，防止 VPN 环境下无限卡死 ---
        socket.setdefaulttimeout(5.0)
        
        print(" 登录 BaoStock 系统...")
        lg = bs.login()
        
        # 恢复默认超时，避免影响后续的长连接数据下载
        socket.setdefaulttimeout(default_timeout)
        
        if lg.error_code != "0":
            print(f"BaoStock 登录失败: {lg.error_msg}")
            return pd.DataFrame()
        
        is_logged_in = True  # 标记登录成功，用于后面的 finally 登出判断
        print("BaoStock 登录成功。")

        # 2. 规整股票代码为 BaoStock 格式
        symbol_clean = symbol.strip().upper()
        if "SH." in symbol_clean or "SZ." in symbol_clean:
            ticker_code = symbol_clean.lower()
        elif symbol_clean.endswith(".SS"):
            ticker_code = f"sh.{symbol_clean.replace('.SS', '').lower()}"
        elif symbol_clean.endswith(".SZ"):
            ticker_code = f"sz.{symbol_clean.replace('.SZ', '').lower()}"
        else:
            # 针对 000001 的特异性补丁
            if symbol_clean == "000001":
                ticker_code = "sz.000001" 
            elif symbol_clean in ["999999", "SH000001"]:
                ticker_code = "sh.000001"
            elif symbol_clean.startswith(("6", "9", "11", "51")):
                ticker_code = f"sh.{symbol_clean.lower()}"
            elif symbol_clean.startswith(("0", "3", "15", "16")):
                ticker_code = f"sz.{symbol_clean.lower()}"
            else:
                ticker_code = f"sh.{symbol_clean.lower()}"

        # 3. 映射 K 线类型
        interval_mapping = {Ktype.DAILY: "d", Ktype.WEEKLY: "w", Ktype.MONTHLY: "m"}
        frequency = interval_mapping.get(kline_type)
        if not frequency:
            raise ValueError(f"kline_type 参数错误！暂不支持该类型: {kline_type}")

        # 4. 期望获取的字段
        fields = "date,open,high,low,close,volume"
        print(f"正在获取 {ticker_code} 的 {kline_type.value} 数据...")

        # 5. 调用 API 获取历史 K 线
        rs = bs.query_history_k_data_plus(
            code=ticker_code,
            fields=fields,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag="3",  # 1:后复权 2:前复权 3:不复权
        )

        if rs.error_code != "0":
            print(f"数据查询失败: {rs.error_msg}")
            return pd.DataFrame()

        # 6. 将数据转换为 pandas DataFrame
        data_list = []
        while (rs.error_code == "0") & rs.next():
            data_list.append(rs.get_row_data())

        df = pd.DataFrame(data_list, columns=rs.fields)

        # 7. 规整格式
        if not df.empty:
            numeric_cols = ["open", "high", "low", "close", "volume"]
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            df.set_index("date", inplace=True)
            df.index = pd.to_datetime(df.index)
            df.index.name = "date"
        return df

    except socket.timeout:
        print("\n[错误] BaoStock 连接超时！")
        print("原因提示: 检测到网络握手失败，请检查是否开启了全局 VPN/翻墙代理。请尝试关闭 VPN 或在代理软件中将国内流量设置为“直连（Direct）”。")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"\n[运行异常] 发生未知错误: {e}")
        return pd.DataFrame()
        
    finally:
        # 确保 socket 超时时间被还原，不影响程序的其他网络模块
        socket.setdefaulttimeout(default_timeout)
        # 8. 只有成功登录了，最后才需要且必须登出系统
        if is_logged_in:
            print(" 登出 BaoStock 系统。")
            bs.logout()




def _get_from_sina(stock_code: str, start_date: str, end_date: str, kline_type: Ktype= Ktype.DAILY) -> pd.DataFrame:
    """
    stock_code : str          股票代码，如 '600000' 或 'sh600000'
    start_date : str          开始日期，格式 'YYYY-MM-DD'
    end_date : str            结束日期，格式 'YYYY-MM-DD'
    klinetype : Ktype             
    Returns:
    --------
    pd.DataFrame
        包含OHLCV数据的DataFrame
    """
           
    def get_stock_symbol(code: str) -> str:
        """转换为新浪格式"""
        # 如果已经包含前缀，直接返回
        if code.startswith(('sh', 'sz')):
            return code.lower()
        
        # === 指数特殊处理 ===
        # 上证指数
        if code=="999999" or code=="sh000001":
            return 'sh000001'
        
        # 深证成指
        if code == '399001':
            return 'sz399001'
        
        # 创业板指
        if code == '399006':
            return 'sz399006'
        
        # 科创50
        if code == '000688':
            return 'sh000688'
        
        # 沪深300
        if code == '000300':
            return 'sh000300'
        
        # === 股票处理 ===
        # 如果要获取中国平安的股票数据，需要使用 '601318'（中国平安的股票代码）
        if code.startswith(('6', '5')):
            return f"sh{code}"
        else:
            return f"sz{code}"

    # 创建session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    })
    
    # 获取日线数据
    try:
        symbol = get_stock_symbol(stock_code)
        url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {
            'symbol': symbol,
            'scale': '240',      # 日线
            'ma': 'no',
            'datalen': '2000'    # 获取足够多数据
        }
        
        response = session.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"HTTP错误: {response.status_code}")
            return pd.DataFrame()
        
        text = response.text
        # 处理可能的JSONP包装
        if text.startswith('/*'):
            text = text[text.find('(')+1:text.rfind(')')]
        
        data = json.loads(text)
        
        if not data or len(data) == 0:
            print("返回数据为空")
            return pd.DataFrame()
        
        # 转换为DataFrame
        records = []
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        for item in data:
            date_str = item.get('day', '')
            if not date_str:
                continue
            
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if start_dt <= date <= end_dt:
                records.append({
                    'date': date,
                    'open': float(item.get('open', 0)),
                    'high': float(item.get('high', 0)),
                    'low': float(item.get('low', 0)),
                    'close': float(item.get('close', 0)),
                    'volume': float(item.get('volume', 0)),
                    # 'amount': 0  # 新浪接口不提供成交额
                })
        
        if not records:
            print(f"指定日期范围内无数据 (范围: {start_date} ~ {end_date})")
            return pd.DataFrame()
        
        df_daily = pd.DataFrame(records)
        df_daily.set_index('date', inplace=True)
        df_daily.sort_index(inplace=True)
        print(f"✓ 获取到 {len(df_daily)} 条日线数据")
        
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        print(f"原始返回: {text[:200] if 'text' in locals() else '无'}")
        return pd.DataFrame()
    except Exception as e:
        print(f"获取日线数据失败: {e}")
        return pd.DataFrame()
    
    # 如果请求日线，直接返回
    if kline_type == Ktype.DAILY:
        return df_daily
    
    # 根据日线数据聚合生成周线或月线
    if kline_type == Ktype.WEEKLY:
        # 周线：使用周五作为周结束
        df = df_daily.resample('W-FRI').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            # 'amount': 'sum'
        })
        df = df.dropna()
        print(f"✓ 从日线聚合生成 {len(df)} 条周线数据")
        return df
    
    elif kline_type == Ktype.MONTHLY:
        # 月线：使用月末
        df = df_daily.resample('ME').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            # 'amount': 'sum'
        })
        df = df.dropna()
        print(f"✓ 从日线聚合生成 {len(df)} 条月线数据")
        return df
    
    else:
        raise ValueError(f"不支持的K线类型: {Ktype}")

def _get_from_yfinance(symbol: str, start_date: str, end_date: str, kline_type:Ktype= Ktype.DAILY):
    # 你之前写的 yfinance 核心逻辑
    """使用 yfinance 获取 A 股指定时间段的 K 线信息
    :param symbol: 股票代码，支持带后缀(如 '600519.SS') 或 纯数字(如 '600519', '000858')
    :param start_date: 开始日期，格式 'YYYY-MM-DD'
    :param end_date: 结束日期，格式 'YYYY-MM-DD'
    :param kline_type: K线类型，可选值: '日K', '周K', '月K'
    :return: 包含K线数据的 pandas DataFrame
    """
    # 1. 自动处理 A 股代码后缀
    symbol = symbol.strip()
    if not (symbol.endswith(".SS") or symbol.endswith(".SZ")):
        if symbol.startswith(("6", "9", "11", "51")):
            ticker_code = f"{symbol}.SS"
        elif symbol.startswith(("0", "3", "15", "16")):
            ticker_code = f"{symbol}.SZ"
        else:
            ticker_code = f"{symbol}.SS"
    else:
        ticker_code = symbol
    if symbol=="sh000001":    #上证指数特珠处理，统一叫sh000001,以区别平安0000001
            ticker_code="000001.SS"

    # 2. 映射 K 线类型
    interval_mapping = {Ktype.DAILY: "1d", Ktype.WEEKLY: "1wk", Ktype.MONTHLY: "1mo"}
    interval = interval_mapping.get(kline_type)
    if not interval:
        raise ValueError("kline_type 参数错误！请选择: '日K', '周K' 或 '月K'")

    # 3. 下载数据
    print(f"正在获取 {ticker_code} 的 {kline_type} 数据 ({start_date} 至 {end_date})...")
    df = yf.download(
        tickers=ticker_code, start=start_date, end=end_date, interval=interval, progress=False
    )

    # 4. 数据后处理（修复 KeyError 核心部分）
    if df.empty:
        print(f"未找到相关数据，请检查代码 {ticker_code} 或日期范围。")
        return df

    # 新版 yfinance 返回的 columns 可能是多级索引 (MultiIndex)，先尝试拍平
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df.columns = df.columns.droplevel(1)
        except Exception:
            # 如果拍平失败，直接取第一层的名字
            df.columns = [col[0] for col in df.columns]

    # 定义我们期望获取的列
    expected_columns = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

    # 动态过滤：只筛选目前 DataFrame 里面确实存在的列，防止报 KeyError
    existing_columns = [col for col in expected_columns if col in df.columns]
    df = df[existing_columns]
    # 1. 直接把所有列名批量变小写
    df.columns = df.columns.str.lower()

    # 2. 顺便把行索引的 'Date' 也变成小写 'date'
    if df.index.name:
        df.index.name = df.index.name.lower()

    df.index.name = "date"
    return df
    
def kdf_to_json(k_df: pd.DataFrame):
    """
    baostock K线DataFrame 转为可直接返回前端的标准列表
    处理浮点、空值、日期格式，避免json序列化报错
    """
    if k_df.empty:
        return []
    
    # 1. 复制副本，不修改原df
    df = k_df.copy()
    
    # 2. baostock date列是数字，统一转字符串日期
    df["date"] = df["date"].astype(str)
    
    # 3. 把所有浮点列转为float，防止decimal类型无法序列化
    float_cols = ["open", "high", "low", "close", "volume", "amount"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # NaN替换为null，前端能识别
            df[col] = df[col].where(df[col].notna(), None)
    # 4. DataFrame -> list[dict]
    data_records = df.to_dict(orient="records")
    return data_records

# ==========================================
# 第二部分：统一对外的核心接口（高级工厂函数）
# ==========================================
def get_kline_data(
    symbol: str,
    start_date: str,
    end_date: str,
    kline_type: Ktype = Ktype.DAILY,
    source: str = "auto",
):
    """统一获取K线数据入口

    :param source: 'yfinance', 'baostock', 'akshare', 'tdx' 或 'auto'(自动轮询)
    """
    # 定义映射字典
    source_map = {
        "yfinance": _get_from_yfinance,
        "baostock": _get_from_baostock,
         "sina": _get_from_sina,
        "tdx": _get_from_tdx,
    }

    # 情况 A：指定了特定的数据源
    if source in source_map:
        return source_map[source](symbol, start_date, end_date, kline_type)

    # 情况 B：高级智能模式（auto）—— 谁行谁上，自动容错
    if source == "auto":
        # 1. 优先尝试本地通达信（速度最快）
        try:
            df = _get_from_tdx(symbol, start_date, end_date, kline_type)
            if not df.empty:
                # df.set_index('date', inplace=True)
                return df
        except Exception:
            print("connection does working well...")

        # 2. 本地没有，尝试最稳定的 BaoStock
        try:
            df = _get_from_baostock(symbol, start_date, end_date, kline_type)
            if not df.empty:
                # df.index = pd.to_datetime(df.index)
                return df
        except Exception:
             print("connection does working well...")

        # 3.选择走新浪
        try:  
            df = _get_from_sina(symbol, start_date, end_date, kline_type)
            if not df.empty:
                return df
        except Exception:
            pass
        #4 yahoo要科学上网，暂不写入

    print("所有数据源获取失败！")
    return pd.DataFrame()

if __name__ == "__main__":
    # 请根据实际情况修改通达信安装路径
    stock_code = '600362'
    start_date = '2026-06-10'
    end_date = '2026-06-23'
    # df=get_kline_data(stock_code, start_date, end_date,Ktype.DAILY,source="tdx")
    # print("上证指数通达信数据源 is OK :")
    # print(df.head(5))
    # print(df.dtypes)
    # print("index的数据类型:  ",df.index.dtype)

    df=get_kline_data('sh000001', start_date, end_date,Ktype.DAILY,source="yfinance")
    # df=_get_from_yfinance('000001', start_date, end_date, Ktype.DAILY)
    print("上证指数 yfinance 数据源: ")
    print(df.head(5))
    print(df.dtypes)
    print("index的数据类型:  ",df.index.dtype)
