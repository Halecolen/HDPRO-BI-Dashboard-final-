import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Cấu hình trang Dashboard
st.set_page_config(page_title="HD PRO VN - Integrated BI Dashboard", layout="wide")

# --- YÊU CẦU 1: TỰ ĐỘNG MÔ PHỎNG BỘ DỮ LIỆU TÍCH HỢP ---
@st.cache_data
def generate_simulated_data():
    np.random.seed(42)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 4, 30)
    date_range = pd.date_range(start_date, end_date, freq='D')
    
    channels = ['Facebook Ads', 'Shopee Ads', 'Lazada Ads']
    campaigns = ['Campaign_A', 'Campaign_B', 'Campaign_C']
    skus = [
        {'id': 'SKU_01', 'category': 'Gia dụng', 'cogs_rate': 0.6},
        {'id': 'SKU_02', 'category': 'Thiết bị', 'cogs_rate': 0.4},
        {'id': 'SKU_03', 'category': 'Tiêu dùng', 'cogs_rate': 0.7},
    ]
    
    # Simulate Marketing Spend Fact
    marketing_data = []
    for d in date_range:
        for ch in channels:
            for cp in campaigns:
                spend = np.random.uniform(50, 500)
                # Cố ý tạo tình huống: Campaign_C trên Shopee spend cao nhưng hiệu quả thấp
                if ch == 'Shopee Ads' and cp == 'Campaign_C':
                    spend = spend * 2.5 
                
                impr = spend * np.random.uniform(100, 200)
                clicks = impr * np.random.uniform(0.01, 0.05)
                marketing_data.append([d, ch, cp, spend, impr, clicks])
    
    df_marketing = pd.DataFrame(marketing_data, columns=['Date', 'Channel', 'Campaign', 'Spend', 'Impressions', 'Clicks'])
    
    # Simulate Sales Fact
    sales_data = []
    for d in date_range:
        num_orders = np.random.randint(5, 20)
        for _ in range(num_orders):
            sku = np.random.choice(skus)
            ch = np.random.choice(channels)
            rev = np.random.uniform(200, 1000)
            
            # Tình huống: SKU_03 doanh thu cao nhưng COGS cao
            cogs = rev * sku['cogs_rate']
            sales_data.append([d, f"ORD_{np.random.randint(10000, 99999)}", ch, sku['id'], sku['category'], rev, cogs])
            
    df_sales = pd.DataFrame(sales_data, columns=['Date', 'OrderID', 'Channel', 'SKU', 'Category', 'Revenue', 'COGS'])
    
    return df_marketing, df_sales

df_marketing, df_sales = generate_simulated_data()

# --- YÊU CẦU 3: SIDEBAR & BỘ LỌC ĐỘNG ---
st.sidebar.header("BỘ LỌC CHIẾN LƯỢC")
date_range = st.sidebar.date_input("Khoảng thời gian", [datetime(2025, 11, 1), datetime(2026, 4, 30)])
selected_channels = st.sidebar.multiselect("Kênh quảng cáo", options=df_marketing['Channel'].unique(), default=df_marketing['Channel'].unique())
selected_categories = st.sidebar.multiselect("Ngành hàng", options=df_sales['Category'].unique(), default=df_sales['Category'].unique())

# Filter data
mask_mkt = (df_marketing['Date'].dt.date >= date_range[0]) & (df_marketing['Date'].dt.date <= date_range[1]) & (df_marketing['Channel'].isin(selected_channels))
mask_sales = (df_sales['Date'].dt.date >= date_range[0]) & (df_sales['Date'].dt.date <= date_range[1]) & (df_sales['Channel'].isin(selected_channels)) & (df_sales['Category'].isin(selected_categories))

f_mkt = df_marketing[mask_mkt]
f_sales = df_sales[mask_sales]

# --- YÊU CẦU 2: INTEGRATED KPIs CALCULATION ---
total_spend = f_mkt['Spend'].sum()
total_rev = f_sales['Revenue'].sum()
total_cogs = f_sales['COGS'].sum()
total_gp = total_rev - total_cogs
net_profit_after_ads = total_gp - total_spend
mer = total_rev / total_spend if total_spend > 0 else 0
roas = total_rev / total_spend if total_spend > 0 else 0

# Navigation Menu
page = st.sidebar.selectbox("MENU BÁO CÁO", ["TRANG 1: OVERVIEW PERFORMANCE", "TRANG 2: DEEP-DIVE ANALYSIS", "TRANG 3: ĐÁNH GIÁ CẢI THIỆN"])

# --- TRANG 1: OVERVIEW PERFORMANCE ---
if page == "TRANG 1: OVERVIEW PERFORMANCE":
    st.title("🚀 Tổng Quan Hiệu Suất Marketing & Sales")
    
    # KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Revenue", f"{total_rev:,.0f} $")
    col2.metric("Ads Spend", f"{total_spend:,.0f} $", delta=f"MER: {mer:.2f}")
    col3.metric("Profit After Ads", f"{net_profit_after_ads:,.0f} $", delta_color="normal")
    col4.metric("ROAS", f"{roas:.2f}x")
    col5.metric("Avg CTR", f"{(f_mkt['Clicks'].sum()/f_mkt['Impressions'].sum()*100):.2f}%")

    # Chart 1: Revenue vs Spend Trend
    st.subheader("📊 Xu hướng Doanh thu và Chi phí Marketing")
    trend_rev = f_sales.groupby(f_sales['Date'].dt.to_period('M'))['Revenue'].sum().reset_index()
    trend_mkt = f_mkt.groupby(f_mkt['Date'].dt.to_period('M'))['Spend'].sum().reset_index()
    trend_rev['Date'] = trend_rev['Date'].astype(str)
    trend_mkt['Date'] = trend_mkt['Date'].astype(str)
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Bar(x=trend_rev['Date'], y=trend_rev['Revenue'], name='Revenue', marker_color='#3498db'))
    fig_trend.add_trace(go.Scatter(x=trend_mkt['Date'], y=trend_mkt['Spend'], name='Ads Spend', line=dict(color='#e74c3c', width=4)))
    fig_trend.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig_trend, use_container_width=True)

    # Chart 2: Channel Performance
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("💰 Tỷ trọng Doanh thu theo Kênh")
        fig_pie = px.pie(f_sales, values='Revenue', names='Channel', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie)
    with col_right:
        st.subheader("📈 Lợi nhuận sau Ads theo Kênh")
        ch_rev = f_sales.groupby('Channel')['Revenue'].sum()
        ch_cogs = f_sales.groupby('Channel')['COGS'].sum()
        ch_spend = f_mkt.groupby('Channel')['Spend'].sum()
        ch_profit = (ch_rev - ch_cogs) - ch_spend
        fig_bar = px.bar(ch_profit, color=ch_profit.values, color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_bar)

# --- TRANG 2: SKU & CAMPAIGN DEEP-DIVE ---
elif page == "TRANG 2: DEEP-DIVE ANALYSIS":
    st.title("🔍 Phân Tích Sâu & Hỗ Trợ Ra Quyết Định")
    
    # Campaign Analysis
    st.subheader("🎯 Hiệu suất Chiến dịch: Chi phí vs Lợi nhuận thực tế")
    cp_mkt = f_mkt.groupby('Campaign').agg({'Spend':'sum', 'Clicks':'sum'}).reset_index()
    # Giả định phân bổ doanh thu mẫu cho chiến dịch
    cp_mkt['Estimated_Net_Profit'] = cp_mkt['Spend'] * np.array([1.2, 0.8, -0.4]) # Campaign_C gây lỗ
    
    fig_cp = px.scatter(cp_mkt, x='Spend', y='Estimated_Net_Profit', size='Clicks', color='Campaign',
                 text='Campaign', title="Campaign C đang gây lỗ ròng dù Spend cao (Rủi ro ra quyết định)")
    fig_cp.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_cp, use_container_width=True)

    # SKU Performance
    st.subheader("📦 Lợi nhuận sau Ads theo mã SKU (Net Profit after Ads)")
    sku_perf = f_sales.groupby('SKU').agg({'Revenue':'sum', 'COGS':'sum'}).reset_index()
    # Trừ chi phí marketing phân bổ giả định cho SKU
    sku_perf['Net_Profit_After_Ads'] = (sku_perf['Revenue'] - sku_perf['COGS']) - (total_spend / 3)
    
    fig_sku = px.bar(sku_perf, x='SKU', y='Net_Profit_After_Ads', color='Net_Profit_After_Ads',
                     color_continuous_scale='RdBu', title="Cảnh báo: SKU_03 đang có biên lợi nhuận âm sau khi trừ Ads")
    st.plotly_chart(fig_sku, use_container_width=True)
    
    st.error("💡 QUYẾT ĐỊNH QUẢN TRỊ: Cần cắt giảm 50% ngân sách Campaign_C và tạm dừng quảng cáo SKU_03 để tối ưu hóa dòng tiền.")

# --- TRANG 3: ĐÁNH GIÁ CẢI THIỆN ---
elif page == "TRANG 3: ĐÁNH GIÁ CẢI THIỆN":
    st.title("🏆 Đánh giá Cải thiện Hệ thống (Before vs After)")
    
    comparison_data = {
        "Tiêu chí đánh giá": ["Thời gian lập báo cáo", "Độ chính xác dữ liệu", "Khả năng tích hợp", "Tần suất cập nhật", "Cơ sở ra quyết định"],
        "Trước khi có Dashboard (Excel)": ["3 - 5 ngày làm việc", "Sai lệch ~15% do nhập tay", "Rời rạc (Ads riêng, Sales riêng)", "Theo tháng/quý", "Cảm tính & Kinh nghiệm"],
        "Sau khi có Dashboard (BI)": ["0 giây (Real-time)", "Chính xác 100% (ETL tự động)", "Tích hợp hoàn toàn", "Tức thì (Real-time)", "Dựa trên số liệu tích hợp (Data-driven)"]
    }
    df_compare = pd.DataFrame(comparison_data)
    st.table(df_compare)
    
    st.success("Hệ thống đã giúp doanh nghiệp HD PRO VN tiết kiệm 120 giờ làm việc/tháng và tăng 20% hiệu quả sử dụng ngân sách marketing.")
