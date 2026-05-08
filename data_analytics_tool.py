import streamlit as st
import pandas as pd
import io

def get_mock_data():
    """Tạo dữ liệu giả lập cho danh sách 100k doanh nghiệp (thu gọn để demo)."""
    data = {
        "MST": ["0101248141", "0314456789", "0300588569", "0100109106", "0301444753", "0311813220", "0108342468"],
        "Tên công ty": ["Công ty TNHH Phần mềm Công nghệ FPT", "Công ty Cổ phần Bán lẻ Minh Tuấn", "Công ty Cổ phần Sữa Việt Nam (Vinamilk)", "Tập đoàn Vingroup", "Công ty Vàng bạc đá quý Phú Nhuận PNJ", "Công ty Cổ phần Thế Giới Di Động", "Công ty TNHH Shopee"],
        "Thành phố": ["Hà Nội", "Hồ Chí Minh", "Hồ Chí Minh", "Hà Nội", "Hồ Chí Minh", "Hồ Chí Minh", "Hà Nội"],
        "Ngành nghề": ["Công nghệ", "Bán lẻ", "Sản xuất Thực phẩm", "Bất động sản", "Bán lẻ", "Bán lẻ", "Thương mại Điện tử"],
        "Doanh thu ước tính (Tỷ VND)": [15000, 200, 60000, 130000, 30000, 100000, 50000],
        "Trạng thái CRM": ["Khách VIP", "Khách mới", "Tiềm năng", "Khách VIP", "Đang tiếp cận", "Tiềm năng", "Chưa liên hệ"]
    }
    return pd.DataFrame(data)

def render_analytics_dashboard():
    st.markdown("### 📊 Data Analytics Dashboard (B2B Records)")
    st.write("Công cụ phân tích và trực quan hóa danh sách mã số thuế doanh nghiệp (Đặc chuẩn cho tệp cào 100.000 doanh nghiệp HN & HCM).")

    # 1. Upload file
    uploaded_file = st.file_uploader("Tải lên danh sách doanh nghiệp (CSV/Excel)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.success(f"Đã tải lên dữ liệu: {uploaded_file.name} thành công!")
        except Exception as e:
            st.error(f"Lỗi khi đọc file: {e}")
            df = get_mock_data()
            st.warning("Đang sử dụng dữ liệu mẫu thay thế.")
    else:
        df = get_mock_data()
        st.info("Chưa có file nào được tải lên. Đang hiển thị **dữ liệu mẫu (Mock Data)**.")

    # 2. Hiển thị số liệu tổng quan (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tổng số doanh nghiệp", f"{len(df):,}")
    
    if "Thành phố" in df.columns:
        col2.metric("Số Tỉnh/Thành", f"{df['Thành phố'].nunique()}")
    else:
        col2.metric("Số Cột Dữ liệu", f"{len(df.columns)}")
        
    if "Ngành nghề" in df.columns:
        col3.metric("Số Ngành nghề", f"{df['Ngành nghề'].nunique()}")
    else:
        col3.metric("Kích thước dữ liệu", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
    missing_data = df.isnull().sum().sum()
    col4.metric("Dữ liệu thiếu (Nulls)", f"{missing_data}")

    st.divider()

    # 3. Layout cho Biểu đồ trực quan
    st.markdown("#### 📈 Trực quan hóa Dữ liệu")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.write("**Phân bố theo Tỉnh/Thành phố**")
        if "Thành phố" in df.columns:
            city_counts = df["Thành phố"].value_counts()
            st.bar_chart(city_counts, color="#FF6B6B")
        else:
            st.write("Không tìm thấy cột 'Thành phố'. Vui lòng chọn file có chuẩn cấu trúc.")

    with col_chart2:
        st.write("**Phân bố theo Ngành nghề**")
        if "Ngành nghề" in df.columns:
            industry_counts = df["Ngành nghề"].value_counts()
            st.bar_chart(industry_counts, color="#4ECDC4")
        else:
            st.write("Không tìm thấy cột 'Ngành nghề'. Vui lòng chọn file có chuẩn cấu trúc.")

    st.divider()

    # 4. Lọc dữ liệu thông minh và Tương tác với Bảng
    st.markdown("#### 🤖 Lọc dữ liệu thông minh & Xuất File")
    
    search_query = st.text_input("🔍 Nhập từ khóa để tìm kiếm (Tên công ty, mã số thuế, ngành nghề, thành phố, ...):", placeholder="VD: Bán lẻ, Hồ Chí Minh, Vinamilk...")
    
    filtered_df = df.copy()
    if search_query:
        # Cỗ máy lọc siêu tốc trên mọi cột chuỗi
        mask = filtered_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        filtered_df = filtered_df[mask]
        st.success(f"🎯 Đã tìm thấy {len(filtered_df)} doanh nghiệp khớp với từ khóa.")
    
    st.dataframe(filtered_df, use_container_width=True)

    # 5. Xuất Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='DanhSachDoanhNghiep')
    
    st.download_button(
        label="📥 Tải xuống dữ liệu đã lọc (.xlsx)",
        data=buffer.getvalue(),
        file_name="B2B_DanhSachDoanhNghiep_Filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
