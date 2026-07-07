/**
 * K线图绘制模块 - 前端完整版本
 * 依赖：Plotly.js (需在HTML中引入)
 */

// ==================== 枚举定义 ====================
const KlineType = {
    DAILY: '日K',
    WEEKLY: '周K',
    MONTHLY: '月K'
};

// ==================== 地支计算工具 ====================
const DizhiUtils = {
    // 日K线地支列表（从1990-12-19开始）
    dizhiList: ['亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌'],
    
    // 月K线地支列表（从1月开始）
    monthDizhiList: ['丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子'],
    
    /**
     * 计算日K线的地支
     * @param {Date} date - 日期对象
     * @returns {string} 地支
     */
    getDailyDizhi(date) {
        const origin = new Date('1990-12-19');
        const diffDays = Math.floor((date - origin) / (24 * 60 * 60 * 1000));
        const index = ((diffDays - 5) % 12 + 12) % 12;
        return this.dizhiList[index];
    },
    
    /**
     * 计算月K线的地支
     * @param {number} month - 月份 (1-12)
     * @returns {string} 地支
     */
    getMonthlyDizhi(month) {
        return this.monthDizhiList[month - 1] || '';
    },
    
    /**
     * 批量计算日K线地支
     * @param {Array<string>} dates - 日期字符串数组
     * @returns {Array<string>} 地支数组
     */
    batchDailyDizhi(dates) {
        return dates.map(dateStr => {
            const date = new Date(dateStr);
            return this.getDailyDizhi(date);
        });
    },
    
    /**
     * 批量计算月K线地支
     * @param {Array<number>} months - 月份数组
     * @returns {Array<string>} 地支数组
     */
    batchMonthlyDizhi(months) {
        return months.map(month => this.getMonthlyDizhi(month));
    }
};

// ==================== 日期范围计算 ====================
class DateRangeCalculator {
    /**
     * 计算日期范围
     * @param {string} baseDate - 基准日期 'YYYY-MM-DD'
     * @param {string} klineType - K线类型 ('日K', '周K', '月K')
     * @param {number} before - 之前的天数/周数/月数
     * @param {number} after - 之后的天数/周数/月数
     * @returns {Object} { start, end }
     */
    static calculate(baseDate, klineType = KlineType.DAILY, before = 10, after = 30) {
        const base = new Date(baseDate);
        
        let start, end;
        
        switch(klineType) {
            case KlineType.DAILY:
                start = new Date(base);
                start.setDate(start.getDate() - before);
                end = new Date(base);
                end.setDate(end.getDate() + after);
                break;
                
            case KlineType.WEEKLY:
                start = new Date(base);
                start.setDate(start.getDate() - before * 7);
                end = new Date(base);
                end.setDate(end.getDate() + after * 7);
                break;
                
            case KlineType.MONTHLY:
                start = new Date(base);
                start.setMonth(start.getMonth() - before);
                end = new Date(base);
                end.setMonth(end.getMonth() + after);
                break;
                
            default:
                throw new Error(`不支持的K线类型: ${klineType}`);
        }
        
        return {
            start: this.formatDate(start),
            end: this.formatDate(end)
        };
    }
    
    /**
     * 格式化日期为 YYYY-MM-DD
     */
    static formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
}

// ==================== K线图绘制器 ====================
class KlineChart {
    /**
     * 绘制K线图
     * @param {Object} params - 参数对象
     * @param {string} params.stockCode - 股票代码
     * @param {string} params.stockName - 股票名称
     * @param {string} params.baseDate - 起卦日期
     * @param {string} params.klineType - K线类型 ('日K', '周K', '月K')
     * @param {Array} params.dates - 日期数组
     * @param {Array} params.opens - 开盘价数组
     * @param {Array} params.highs - 最高价数组
     * @param {Array} params.lows - 最低价数组
     * @param {Array} params.closes - 收盘价数组
     * @param {string} params.containerId - 容器ID，默认 'klineContainer'
     * @param {number} params.width - 宽度，默认 800
     * @param {number} params.height - 高度，默认 600
     * @param {Object} params.colors - 颜色配置
     * @returns {Promise} Plotly Promise
     */
    static async draw(params) {
        const {
            stockCode = '',
            stockName = '',
            baseDate = '',
            klineType = KlineType.DAILY,
            dates = [],
            opens = [],
            highs = [],
            lows = [],
            closes = [],
            containerId = 'klineContainer',
            width = 800,
            height = 600,
            colors = { increasing: '#ef5350', decreasing: '#26a69a' }
        } = params;

        // 验证数据
        if (!dates || dates.length === 0) {
            console.error('数据为空');
            return Promise.reject('数据为空');
        }

        console.log(`绘制K线图: ${stockCode} ${stockName}, 数据量: ${dates.length}`);

        // 1. 计算日期数字和地支
        let days = [];
        let dizhi = [];
        
        if (klineType === KlineType.DAILY) {
            // 日K线：显示日期数字和地支
            days = dates.map(d => new Date(d).getDate());
            dizhi = DizhiUtils.batchDailyDizhi(dates);
        } else if (klineType === KlineType.MONTHLY) {
            // 月K线：显示月份和地支
            days = dates.map(d => new Date(d).getMonth() + 1);
            dizhi = DizhiUtils.batchMonthlyDizhi(days);
        } else if (klineType === KlineType.WEEKLY) {
            // 周K线：只显示月份，不显示地支
            days = dates.map(d => new Date(d).getMonth() + 1);
            dizhi = new Array(dates.length).fill('');
        }

        // 2. 计算标记位置（起卦日期标注）
        const markResult = this.calculateMarkPosition(dates, highs, baseDate);
        const { markDay, markPos } = markResult;
        console.log('标记日期:', markDay, '标记位置:', markPos);

        // 3. 计算地支和日期的显示位置
        const maxHigh = Math.max(...highs);
        const minLow = Math.min(...lows);
        const amp = (maxHigh - minLow) / minLow;
        const posDizhi = 1 - amp / 12;
        const posDay = posDizhi - amp / 12;

        // 4. 创建图表数据
        const traces = this.buildTraces(dates, opens, highs, lows, closes, 
                                       dizhi, days, posDizhi, posDay, colors);

        // 5. 构建布局
        const layout = this.buildLayout(stockCode, stockName, klineType, baseDate,
                                       markDay, markPos, dates, width, height);

        // 6. 日K线：移除休市日期
        if (klineType === KlineType.DAILY) {
            const vacationList = this.calculateVacationDates(dates);
            if (vacationList.length > 0) {
                layout.xaxis.rangebreaks = [{ values: vacationList }];
            }
        }

        // 7. 渲染图表
        return this.renderChart(containerId, traces, layout);
    }

    /**
     * 构建图表数据
     */
    static buildTraces(dates, opens, highs, lows, closes, dizhi, days, posDizhi, posDay, colors) {
        const traces = [];

        // K线图
        traces.push({
            type: 'candlestick',
            x: dates,
            open: opens,
            high: highs,
            low: lows,
            close: closes,
            name: 'K线',
            increasing: {
                line: { color: colors.increasing },
                fillcolor: colors.increasing
            },
            decreasing: {
                line: { color: colors.decreasing },
                fillcolor: colors.decreasing
            }
        });

        // 地支标注
        if (dizhi && dizhi.length > 0 && dizhi.some(d => d !== '')) {
            const dizhiY = lows.map(low => low * posDizhi);
            traces.push({
                type: 'scatter',
                x: dates,
                y: dizhiY,
                mode: 'text',
                name: '地支',
                text: dizhi,
                textfont: { size: 10, color: 'black' },
                showlegend: false,
                hoverinfo: 'skip'
            });
        }

        // 日期标注
        if (days && days.length > 0) {
            const dayY = lows.map(low => low * posDay);
            traces.push({
                type: 'scatter',
                x: dates,
                y: dayY,
                mode: 'text',
                name: '日期',
                text: days,
                textfont: { size: 10, color: 'blue' },
                showlegend: false,
                hoverinfo: 'skip'
            });
        }

        return traces;
    }

    /**
     * 构建布局
     */
    static buildLayout(stockCode, stockName, klineType, baseDate, markDay, markPos, dates, width, height) {
        const layout = {
            title: {
                text: `${stockCode}${stockName}-${klineType}线     起卦时间: ${baseDate}`,
                x: 0.2,
                y: 0.99,
                xanchor: 'left',
                font: { size: 12, color: 'black' }
            },
            showlegend: false,
            xaxis: {
                type: 'date',
                showgrid: true,
                showticklabels: true,
                gridcolor: 'lightgrey',
                rangeslider: { visible: false }
            },
            yaxis: {
                showgrid: true,
                showticklabels: true,
                gridcolor: 'lightgrey'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            width: width,
            height: height,
            margin: { l: 20, r: 10, t: 30, b: 10 },
            annotations: []
        };

        // 添加标记箭头
        if (markPos !== null && markDay) {
            layout.annotations.push({
                x: markDay,
                y: markPos,
                xref: 'x',
                yref: 'y',
                text: '',
                xanchor: 'right',
                yanchor: 'bottom',
                showarrow: true,
                arrowhead: 1,
                arrowsize: 1,
                arrowwidth: 2
            });
        }

        return layout;
    }

    /**
     * 计算标记位置
     */
    static calculateMarkPosition(dates, highs, baseDate) {
        const markDateObj = new Date(baseDate);
        const markDateStr = this.formatDate(markDateObj);
        
        // 查找精确匹配
        const index = dates.indexOf(markDateStr);
        if (index !== -1) {
            return { markDay: markDateStr, markPos: highs[index] };
        }
        
        // 查找最近的日期
        for (let i = 0; i < dates.length; i++) {
            const dateObj = new Date(dates[i]);
            if (dateObj > markDateObj) {
                return { markDay: dates[i], markPos: highs[i] };
            }
        }
        
        return { markDay: null, markPos: null };
    }

    /**
     * 计算休市日期（日K线用）
     */
    static calculateVacationDates(dates) {
        if (!dates || dates.length === 0) return [];
        
        // 生成完整日期范围
        const startDate = new Date(dates[0]);
        const endDate = new Date(dates[dates.length - 1]);
        const fullDateRange = [];
        
        const currentDate = new Date(startDate);
        while (currentDate <= endDate) {
            fullDateRange.push(this.formatDate(currentDate));
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        // 找出缺失的日期（非交易日）
        const dateSet = new Set(dates);
        return fullDateRange.filter(d => !dateSet.has(d));
    }

    /**
     * 格式化日期
     */
    static formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    /**
     * 渲染图表
     */
    static renderChart(containerId, traces, layout) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`容器 ${containerId} 未找到`);
            return Promise.reject(`容器 ${containerId} 未找到`);
        }

        // 清空容器
        container.innerHTML = '';

        // 创建绘图容器
        const plotDiv = document.createElement('div');
        plotDiv.id = `plot-${Date.now()}`;
        plotDiv.style.width = '100%';
        plotDiv.style.height = '100%';
        container.appendChild(plotDiv);

        // 使用 Plotly 绘制
        return Plotly.newPlot(plotDiv, traces, layout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['toImage', 'sendDataToCloud']
        });
    }

    /**
     * 更新图表数据
     */
    static async update(containerId, newData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`容器 ${containerId} 未找到`);
            return;
        }

        const plotDiv = container.querySelector('.js-plotly-plot');
        if (!plotDiv) {
            console.error('Plotly 图表未找到');
            return;
        }

        const updateData = {
            x: [newData.dates],
            open: [newData.opens],
            high: [newData.highs],
            low: [newData.lows],
            close: [newData.closes]
        };

        return Plotly.update(plotDiv, updateData);
    }

    /**
     * 重置图表大小
     */
    static resize(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const plotDiv = container.querySelector('.js-plotly-plot');
        if (plotDiv) {
            Plotly.Plots.resize(plotDiv);
        }
    }

    /**
     * 导出为图片
     */
    static async toImage(containerId, format = 'png') {
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        const plotDiv = container.querySelector('.js-plotly-plot');
        if (!plotDiv) return null;
        
        return Plotly.toImage(plotDiv, { format: format });
    }
}

// ==================== 数据获取和绘图主函数 ====================
class KlineManager {
    /**
     * 获取并绘制K线图
     * @param {Object} params
     * @param {string} params.stockCode - 股票代码
     * @param {string} params.baseDate - 基准日期
     * @param {string} params.klineType - K线类型
     * @param {number} params.before - 之前天数
     * @param {number} params.after - 之后天数
     * @param {string} params.containerId - 容器ID
     * @param {Function} params.dataFetcher - 数据获取函数
     * @returns {Promise}
     */
    static async drawKline(params) {
        const {
            stockCode,
            baseDate,
            klineType = KlineType.DAILY,
            before = 10,
            after = 30,
            containerId = 'klineContainer',
            dataFetcher = null
        } = params;

        try {
            // 1. 计算日期范围
            const dateRange = DateRangeCalculator.calculate(baseDate, klineType, before, after);
            console.log('日期范围:', dateRange);

            // 2. 获取数据（如果提供了数据获取函数）
            let klineData;
            if (dataFetcher) {
                klineData = await dataFetcher({
                    stockCode,
                    startDate: dateRange.start,
                    endDate: dateRange.end,
                    klineType
                });
            } else {
                // 如果没有提供数据获取函数，使用模拟数据（仅用于测试）
                klineData = this.generateMockData(dateRange.start, dateRange.end, klineType);
            }

            // 3. 绘制图表
            await KlineChart.draw({
                stockCode: klineData.stockCode || stockCode,
                stockName: klineData.stockName || '',
                baseDate: baseDate,
                klineType: klineType,
                dates: klineData.dates,
                opens: klineData.opens,
                highs: klineData.highs,
                lows: klineData.lows,
                closes: klineData.closes,
                containerId: containerId
            });

            console.log('K线图绘制完成');
            return klineData;

        } catch (error) {
            console.error('绘制K线图失败:', error);
            throw error;
        }
    }

    /**
     * 生成模拟数据（仅用于测试）
     */
    static generateMockData(startDate, endDate, klineType) {
        const dates = [];
        const opens = [];
        const highs = [];
        const lows = [];
        const closes = [];
        
        let currentDate = new Date(startDate);
        const end = new Date(endDate);
        let price = 100;
        
        while (currentDate <= end) {
            // 跳过周末（仅日K线）
            if (klineType === KlineType.DAILY) {
                const dayOfWeek = currentDate.getDay();
                if (dayOfWeek === 0 || dayOfWeek === 6) {
                    currentDate.setDate(currentDate.getDate() + 1);
                    continue;
                }
            }
            
            dates.push(KlineChart.formatDate(currentDate));
            
            // 生成模拟价格
            const change = (Math.random() - 0.5) * 4;
            const open = price;
            const close = price + change;
            const high = Math.max(open, close) + Math.random() * 2;
            const low = Math.min(open, close) - Math.random() * 2;
            
            opens.push(open);
            closes.push(close);
            highs.push(high);
            lows.push(low);
            
            price = close;
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        return {
            stockCode: '000001',
            stockName: '测试股票',
            dates: dates,
            opens: opens,
            highs: highs,
            lows: lows,
            closes: closes
        };
    }
}

// ==================== 导出 ====================
// 支持浏览器全局使用
if (typeof window !== 'undefined') {
    window.KlineType = KlineType;
    window.DizhiUtils = DizhiUtils;
    window.DateRangeCalculator = DateRangeCalculator;
    window.KlineChart = KlineChart;
    window.KlineManager = KlineManager;
}

// 支持模块化导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        KlineType,
        DizhiUtils,
        DateRangeCalculator,
        KlineChart,
        KlineManager
    };
}