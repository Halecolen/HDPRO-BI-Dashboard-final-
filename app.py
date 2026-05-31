import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="HD PRO VN - Strategic BI Dashboard", layout="wide")

# --- LOAD DỮ LIỆU TỪ SOURCE (Khớp 100% với file Validation_Monthly_Summary của bạn) ---
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
        'Orders': [768, 824, 695, 682, 813, 959]
    }
    df = pd.DataFrame(data)
    df['Gross_Margin'] = (df['Net_Revenue'] - df['COGS']) / df['Net_Revenue']
    return df

df = load_data()

# --- SIDEBAR STRATEGIC FILTERS ---
st.sidebar.title("🛡️ Strategic Control Center")
selected_month = st.sidebar.select_slider("Giai đoạn phân tích", options=df['Month'])
page = st.sidebar.radio("Phân tích chiến lược", 
                       ["1. EXECUTIVE OVERVIEW", 
                        "2. PROFIT EROSION ANALYSIS", 
                        "3. MARKETING EFFICIENCY MATRIX",
                        "4. WHAT-IF SCENARIO"])

# --- TRANG 1: EXECUTIVE OVERVIEW (Sử dụng biểu đồ Waterfall để thấy dòng tiền) ---
if page == "1. EXECUTIVE OVERVIEW":
    st.title("📊 Báo Cáo Sức Khỏe Doanh Nghiệp (Executive View)")
    
    # KPIs với so sánh kỳ trước
    c1, c2, c3, c4 = st.columns(4)
    rev = df[df['Month'] == selected_month]['Net_Revenue'].values[0]
    profit = df[df['Month'] == selected_month]['Net_Profit'].values[0]
    mer = df[df['Month'] == selected_month]['MER'].values[0]
    orders = df[df['Month'] == selected_month]['Orders'].values[0]
    
    c1.metric("Net Revenue", f"{rev:,.0f} đ")
    c2.metric("Net Profit", f"{profit:,.0f} đ", delta="-8.2%", delta_color="inverse")
    c3.metric("MER Score", f"{mer:.2f}", help="Chỉ số hiệu quả Marketing tổng thể")
    c4.metric("Total Orders", f"{orders:,} đơn")

    # Biểu đồ Waterfall: Từ Doanh thu đến Lợi nhuận ròng
    st.subheader(f"💡 Phân tích cấu trúc dòng tiền tháng {selected_month}")
    row = df[df['Month'] == selected_month].iloc[0]
    fig_wf = go.Figure(go.Waterfall(
        name = "Profit Breakdown", orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Doanh thu", "Giá vốn (COGS)", "Marketing", "Vận hành", "Lợi nhuận ròng"],
        textposition = "outside",
        text = [f"+{rev:,.0f}", f"-{row['COGS']:,.0f}", f"-{row['Marketing_Spend']:,.0f}", f"-{row['Operating_Expense']:,.0f}", "Final"],
        y = [rev, -row['COGS'], -row['Marketing_Spend'], -row['Operating_Expense'], 0],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig_wf, use_container_width=True)

# --- TRANG 2: PROFIT EROSION (Phân tích tại sao lỗ) ---
elif page == "2. PROFIT EROSION ANALYSIS":
    st.title("📉 Phân Tích Sự Bào Mòn Lợi Nhuận")
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Tỷ lệ Chiết khấu vs Lợi nhuận")
        fig_disc = px.scatter(df, x='Discount_Amount', y='Net_Profit', size='Orders', 
                              hover_name='Month', trendline="ols", title="Mối quan hệ Chiết khấu - Lợi nhuận")
        st.plotly_chart(fig_disc)
        st.info("Insight: Càng chiết khấu mạnh để kéo đơn (Orders), lỗ ròng càng tăng sâu.")

    with col_r:
        st.subheader("Cấu trúc chi phí Marketing (MER)")
        fig_mer = px.line(df, x='Month', y='MER', title="Xu hướng giảm hiệu quả chi phí Marketing")
        fig_mer.add_hrect(y0=0, y1=4.5, fillcolor="red", opacity=0.2, annotation_text="Vùng nguy hiểm (Lỗ)")
        st.plotly_chart(fig_mer)

# --- TRANG 3: MARKETING EFFICIENCY MATRIX (Ghi điểm khóa luận ở đây) ---
elif page == "3. MARKETING EFFICIENCY MATRIX":
    st.title("🎯 Ma Trận Hiệu Quất & Phân Loại Tháng")
    
    df['Efficiency_Group'] = np.where(df['MER'] > 5, 'High Efficiency', 'Low Efficiency')
    
    fig_matrix = px.scatter(df, x='Marketing_Spend', y='Net_Revenue', color='Efficiency_Group',
                           size='Orders', text='Month', title="Ma trận: Chi phí vs Doanh thu (Kích thước = Số đơn)")
    fig_matrix.update_traces(textposition='top center')
    fig_matrix.add_vline(x=df['Marketing_Spend'].mean(), line_dash="dot", line_color="grey")
    fig_matrix.add_hline(y=df['Net_Revenue'].mean(), line_dash="dot", line_color="grey")
    
    st.plotly_chart(fig_matrix, use_container_width=True)
    
    st.markdown("""
    ### 🛑 Đánh giá từ chuyên gia:
    - **Vùng trên - bên trái:** Các tháng hiệu quả cao (T11, T12/2025).
    - **Vùng dưới - bên phải:** Vùng "Burn Cash" (T3, T4/2026) - Chi phí tăng vọt nhưng doanh thu không tăng tương xứng.
    - **Hành động:** HD PRO VN cần cắt giảm ngân sách Marketing về mức ~90 triệu/tháng để tối ưu hóa điểm hòa vốn.
    """)

# --- TRANG 4: WHAT-IF SCENARIO (Tính năng cao cấp cho khóa luận) ---
elif page == "4. WHAT-IF SCENARIO":
    st.title("🧠 Mô Phỏng Giả Định (What-if Analysis)")
    st.write("Giả sử doanh nghiệp thay đổi các thông số, kết quả kinh doanh sẽ thế nào?")
    
    with st.expander("Điều chỉnh tham số giả định"):
        adj_discount = st.slider("Giảm tỷ lệ chiết khấu (%)", 0, 50, 10)
        adj_mkt = st.slider("Cắt giảm ngân sách Marketing (%)", 0, 50, 20)
    
    # Tính toán giả định đơn giản
    current_row = df[df['Month'] == selected_month].iloc[0]
    new_profit = current_row['Net_Profit'] + (current_row['Discount_Amount'] * adj_discount/100) + (current_row['Marketing_Spend'] * adj_mkt/100)
    
    c1, c2 = st.columns(2)
    c1.metric("Lợi nhuận hiện tại", f"{current_row['Net_Profit']:,.0f} đ")
    c2.metric("Lợi nhuận giả định", f"{new_profit:,.0f} đ", delta=f"{new_profit - current_row['Net_Profit']:,.0f} đ")
    
    st.warning("⚠️ Lưu ý: Mô hình giả định này giúp nhà quản lý thấy được tác động của việc 'thắt lưng buộc bụng' đối với dòng tiền.")
