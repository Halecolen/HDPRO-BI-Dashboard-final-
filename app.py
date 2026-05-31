import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="HD PRO VN - Strategic BI Dashboard", layout="wide")

# --- LOAD DỮ LIỆU TỪ SOURCE (Dữ liệu thực tế từ Validation_Monthly_Summary.csv) ---
@st.cache_data
def load_data():
    data = {
        'Month': ['2025-11', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04'],
        'Net_Revenue': [477739449, 555582681, 476715743, 459777533, 532662885, 621135630],
        'Marketing_Spend': [76312046, 95099837, 93737285, 84668069, 123339999, 139266802],
        'Discount_Amount': [72618942, 80911555, 73201014, 71179401, 82903500, 93031744],
        'COGS': [391260000, 451140000, 392795000, 373710000, 442050000, 505315000],
        'Operating_Expense': [65000000, 68000000, 70000000, 70000000, 75000000, 78000000],
        'Net_Profit': [-121501390, -135721841, -144856995, -132641928, -181994432, -187473491],
        'MER': [6.26, 5.84, 5.08, 5.43, 4.31, 4.46],
        'Orders': [768, 824, 695, 682, 813, 959],
        'CTR': [0.0266, 0.0254, 0.0247, 0.0254, 0.0248, 0.0252]
    }
    df = pd.DataFrame(data)
    # Tính toán thêm các chỉ số hiệu quả
    df['Profit_Margin'] = df['Net_Profit'] / df['Net_Revenue']
    df['Marketing_Intensity'] = df['Marketing_Spend'] / df['Net_Revenue']
    return df

df = load_data()

# --- SIDEBAR: TRUNG TÂM ĐIỀU KHIỂN CHIẾN LƯỢC ---
st.sidebar.markdown("## 🛡️ HD PRO VN STRATEGY")
selected_month = st.sidebar.select_slider("Giai đoạn phân tích", options=df['Month'])
page = st.sidebar.radio("Phân tích chuyên sâu", 
                       ["1. EXECUTIVE WATERFALL", 
                        "2. PROFIT EROSION (REGRESSION)", 
                        "3. EFFICIENCY MATRIX & SEGMENTATION",
                        "4. STRATEGIC WHAT-IF SCENARIO"])

# --- TRANG 1: EXECUTIVE WATERFALL (Phân tích cấu trúc lợi nhuận) ---
if page == "1. EXECUTIVE WATERFALL":
    st.title("📊 Cấu Trúc Lợi Nhuận Chiến Lược")
    st.markdown("Biểu đồ Waterfall giúp nhận diện các yếu tố làm giảm dòng tiền từ Doanh thu xuống Lợi nhuận ròng.")
    
    # KPIs Top Row
    row = df[df['Month'] == selected_month].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Revenue", f"{row['Net_Revenue']:,.0f} đ")
    c2.metric("MER Score", f"{row['MER']:.2f}", help="Chỉ số hiệu quả Marketing (Revenue/Spend)")
    c3.metric("Net Profit", f"{row['Net_Profit']:,.0f} đ", delta="-5.4%")
    c4.metric("Conversion (CTR)", f"{row['CTR']*100:.2f}%")

    # Waterfall Chart
    fig_wf = go.Figure(go.Waterfall(
        name = "Breakdown", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Doanh thu", "Giá vốn (COGS)", "Marketing Spend", "Chi phí vận hành", "Lợi nhuận ròng"],
        textposition = "outside",
        text = [f"+{row['Net_Revenue']:,.0f}", f"-{row['COGS']:,.0f}", f"-{row['Marketing_Spend']:,.0f}", f"-{row['Operating_Expense']:,.0f}", "KẾT QUẢ"],
        y = [row['Net_Revenue'], -row['COGS'], -row['Marketing_Spend'], -row['Operating_Expense'], 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    fig_wf.update_layout(title=f"Phân tích dòng tiền tháng {selected_month}", template="plotly_white", height=500)
    st.plotly_chart(fig_wf, use_container_width=True)

# --- TRANG 2: PROFIT EROSION (Hồi quy tuyến tính OLS) ---
elif page == "2. PROFIT EROSION (REGRESSION)":
    st.title("📉 Phân Tích Sự Bào Mòn Lợi Nhuận")
    st.markdown("Sử dụng mô hình hồi quy OLS để tìm ra tác nhân chính gây lỗ ròng.")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Hồi quy: Chiết khấu vs Lợi nhuận")
        fig_disc = px.scatter(df, x='Discount_Amount', y='Net_Profit', 
                              size='Orders', hover_name='Month',
                              trendline="ols", # Cần statsmodels trong requirements.txt
                              color='MER', 
                              color_continuous_scale='RdYlGn',
                              title="Tương quan Chiết khấu - Lợi nhuận")
        st.plotly_chart(fig_disc, use_container_width=True)
        st.info("Insight: Đường xu hướng đi xuống cho thấy việc lạm dụng chiết khấu để kéo đơn đang trực tiếp làm giảm lợi nhuận.")

    with col_r:
        st.subheader("Hiệu quả Marketing (MER) theo thời gian")
        fig_mer = px.area(df, x='Month', y='MER', title="Xu hướng chỉ số MER")
        fig_mer.add_hline(y=5.0, line_dash="dash", line_color="red", annotation_text="Ngưỡng an toàn (MER=5)")
        st.plotly_chart(fig_mer, use_container_width=True)

# --- TRANG 3: EFFICIENCY MATRIX (Ma trận phân loại tháng) ---
elif page == "3. EFFICIENCY MATRIX & SEGMENTATION":
    st.title("🎯 Ma Trận Hiệu Quất Marketing")
    st.markdown("Phân loại các giai đoạn kinh doanh dựa trên sự tương quan giữa Chi phí và Doanh thu.")
    
    df['Efficiency_Level'] = np.where(df['MER'] > 5.5, 'Tối ưu', 'Kém hiệu quả')
    
    fig_matrix = px.scatter(df, x='Marketing_Spend', y='Net_Revenue', 
                           color='Efficiency_Level', size='Orders', text='Month',
                           labels={'Marketing_Spend': 'Chi phí Marketing', 'Net_Revenue': 'Doanh thu ròng'},
                           title="Ma trận Chiến lược: Chi phí vs Doanh thu")
    
    # Thêm các đường trung bình để tạo thành 4 góc phần tư
    fig_matrix.add_vline(x=df['Marketing_Spend'].mean(), line_dash="dot", line_color="grey")
    fig_matrix.add_hline(y=df['Net_Revenue'].mean(), line_dash="dot", line_color="grey")
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    st.error("💡 PHÂN TÍCH KHÓA LUẬN: Tháng 3 và Tháng 4 năm 2026 nằm trong vùng 'High Spend - Low Efficiency'. Khuyến nghị doanh nghiệp HD PRO VN cần giảm 15-20% ngân sách quảng cáo để tìm lại điểm hòa vốn.")

# --- TRANG 4: STRATEGIC WHAT-IF (Hỗ trợ ra quyết định) ---
elif page == "4. STRATEGIC WHAT-IF SCENARIO":
    st.title("🧠 Mô Phỏng Kịch Bản Quyết Định")
    st.write("Nếu chúng ta thay đổi các biến số vận hành, lợi nhuận ròng sẽ được cải thiện thế nào?")
    
    # Sidebar cho What-if
    with st.sidebar:
        st.markdown("---")
        st.subheader("Biến số giả định")
        cut_discount = st.slider("Cắt giảm Chiết khấu (%)", 0, 50, 20)
        cut_marketing = st.slider("Tối ưu Marketing Spend (%)", 0, 50, 15)
        save_op_ex = st.slider("Tiết kiệm CP Vận hành (%)", 0, 30, 10)
    
    current_data = df[df['Month'] == selected_month].iloc[0]
    
    # Tính toán lợi nhuận giả định
    recovered_discount = current_data['Discount_Amount'] * (cut_discount / 100)
    recovered_mkt = current_data['Marketing_Spend'] * (cut_marketing / 100)
    recovered_opex = current_data['Operating_Expense'] * (save_op_ex / 100)
    
    simulated_profit = current_data['Net_Profit'] + recovered_discount + recovered_mkt + recovered_opex
    
    col_a, col_b = st.columns(2)
    col_a.metric("Lợi nhuận hiện tại", f"{current_data['Net_Profit']:,.0f} đ")
    col_b.metric("Lợi nhuận SAU TỐI ƯU", f"{simulated_profit:,.0f} đ", 
                 delta=f"{simulated_profit - current_data['Net_Profit']:,.0f} đ", delta_color="normal")
    
    # Biểu đồ so sánh
    comparison = pd.DataFrame({
        'Kịch bản': ['Hiện tại', 'Sau tối ưu'],
        'Lợi nhuận': [current_data['Net_Profit'], simulated_profit]
    })
    fig_sim = px.bar(comparison, x='Kịch bản', y='Lợi nhuận', color='Kịch bản', 
                     color_discrete_map={'Hiện tại': '#e74c3c', 'Sau tối ưu': '#2ecc71'})
    st.plotly_chart(fig_sim, use_container_width=True)
    
    st.success(f"Bằng cách tối ưu hóa các chi phí không hiệu quả, HD PRO VN có thể thu hồi lại {recovered_discount + recovered_mkt + recovered_opex:,.0f} VND trong tháng {selected_month}.")
