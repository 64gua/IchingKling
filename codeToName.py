import pandas as pd
import os

# 定义常量，CSV文件名
STOCK_CSV_FILE = 'stock_and_etf.csv'
# BASE_DIR=os.path.dirname(os.path.abspath(__file__))
# STOCK_CSV_FILE=os.path.join(BASE_DIR,"stock_and_etf.csv")

def get_stock_tuple(search_term):
    """
    根据股票代码或股票名称查找对应的股票信息，返回(code, name)元组
    
    参数:
    search_term (str): 要搜索的内容，可以是股票代码或股票名称
    
    返回:
    tuple: (股票代码, 股票名称) 元组，如果未找到则返回None
    """
    # 检查文件是否存在
    if not os.path.exists(STOCK_CSV_FILE):
        raise FileNotFoundError(f"文件 {STOCK_CSV_FILE} 不存在")
    
    try:
        # 读取CSV文件
        df = pd.read_csv(STOCK_CSV_FILE, dtype=str)  # 将所有列读为字符串类型
    except Exception as e:
        raise ValueError(f"读取CSV文件时出错: {e}")
    
    # 确保列名正确
    if len(df.columns) < 2:
        raise ValueError("CSV文件需要至少包含两列：股票代码和股票名称")
    
    # 假设第一列是股票代码，第二列是股票名称
    code_col = df.columns[0]
    name_col = df.columns[1]
    
    # 去除搜索项的首尾空格
    search_term = str(search_term).strip()
    
    # 在代码列中查找
    code_match = df[df[code_col] == search_term]
    
    # 在名称列中查找
    name_match = df[df[name_col] == search_term]
    
    # 如果找到匹配项
    if not code_match.empty:
        code = code_match.iloc[0][code_col]
        name = code_match.iloc[0][name_col]
        return (code, name)
    elif not name_match.empty:
        code = name_match.iloc[0][code_col]
        name = name_match.iloc[0][name_col]
        return (code, name)
    else:
        # 如果没有精确匹配
        print(f"未找到精确匹配的 '{search_term}'")
        return (search_term,"暂无匹配")


# 更健壮的版本，支持模糊搜索
def get_stock_tuple_fuzzy(search_term, fuzzy_match=True):
    """
    根据股票代码或股票名称查找对应的股票信息，返回(code, name)元组
    支持模糊搜索
    
    参数:
    search_term (str): 要搜索的内容，可以是股票代码或股票名称
    fuzzy_match (bool): 是否启用模糊匹配
    
    返回:
    tuple: (股票代码, 股票名称) 元组，如果未找到则返回None
    """
    # 检查文件是否存在
    if not os.path.exists(STOCK_CSV_FILE):
        raise FileNotFoundError(f"文件 {STOCK_CSV_FILE} 不存在")
    
    try:
        # 读取CSV文件
        df = pd.read_csv(STOCK_CSV_FILE, dtype=str)
    except Exception as e:
        raise ValueError(f"读取CSV文件时出错: {e}")
    
    if len(df.columns) < 2:
        raise ValueError("CSV文件需要至少包含两列：股票代码和股票名称")
    
    code_col = df.columns[0]
    name_col = df.columns[1]
    
    search_term = str(search_term).strip()
    
    # 精确匹配
    code_match = df[df[code_col] == search_term]
    name_match = df[df[name_col] == search_term]
    
    if not code_match.empty:
        code = code_match.iloc[0][code_col]
        name = code_match.iloc[0][name_col]
        return (code, name)
    elif not name_match.empty:
        code = name_match.iloc[0][code_col]
        name = name_match.iloc[0][name_col]
        return (code, name)
    elif fuzzy_match:
        # 模糊匹配：在名称中查找包含搜索词的行
        fuzzy_matches = df[df[name_col].str.contains(search_term, case=False, na=False)]
        if not fuzzy_matches.empty:
            code = fuzzy_matches.iloc[0][code_col]
            name = fuzzy_matches.iloc[0][name_col]
            print(f"找到模糊匹配: ({code}, {name})")
            return (code, name)
        else:
            print(f"未找到匹配 '{search_term}' 的股票")
            return None
    else:
        print(f"未找到精确匹配的 '{search_term}'")
        return None


# 添加一个函数，用于格式化为"代码-名称"字符串（如果需要的话）
def format_stock_tuple(stock_tuple):
    """
    将股票元组格式化为"代码-名称"字符串
    
    参数:
    stock_tuple (tuple): (股票代码, 股票名称) 元组
    
    返回:
    str: "股票代码-股票名称"格式的字符串
    """
    if stock_tuple is None:
        return None
    return f"{stock_tuple[0]}-{stock_tuple[1]}"


# 示例使用方式
if __name__ == "__main__":
    # 使用示例
    try:
        print(f"使用CSV文件: {STOCK_CSV_FILE}")
        
        # 精确匹配
        result1 = get_stock_tuple("601111")
        print(f"结果1 (元组): {result1}")
        print(f"结果1 (格式化): {format_stock_tuple(result1) if result1 else None}")
        
        result2 = get_stock_tuple("中国国航")
        print(f"结果2 (元组): {result2}")
        print(f"结果2 (格式化): {format_stock_tuple(result2) if result2 else None}")
        
        # 使用模糊搜索版本
        result3 = get_stock_tuple_fuzzy("思源", fuzzy_match=True)
        print(f"结果3 (元组): {result3}")
        print(f"结果3 (格式化): {format_stock_tuple(result3) if result3 else None}")
        
        # 直接使用元组
        if result1:
            code, name = result1
            print(f"拆包: 代码={code}, 名称={name}")
            
        # 测试不存在的情况
        result4 = get_stock_tuple("不存在的股票")
        print(f"不存在的股票: {result4}")
            
    except Exception as e:
        print(f"发生错误: {e}")
