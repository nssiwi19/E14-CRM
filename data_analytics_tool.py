import streamlit as st
import pandas as pd
import io

try:
    from database import supabase
except ImportError:
    supabase = None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_enterprises_from_supabase():
    """Hàm tải dữ liệu từ Supabase sử dụng cơ chế Pagination và Caching."""
    if not supabase:
        return pd.DataFrame()
    
    table_name = "doanh_nghiep"
    all_data = []
    page_size = 1000
    start = 0
    
    while True:
        # Lấy từng đoạn (chunk) 1000 bản ghi để tránh bị Timeout API
        response = supabase.table(table_name).select("*").range(start, start + page_size - 1).execute()
        data = response.data
        if not data:
            break
        all_data.extend(data)
        
        # Nếu số bản ghi lấy về nhỏ hơn page_size nghĩa là đã lấy hết
        if len(data) < page_size:
            break
        start += page_size
        
        # Giới hạn an toàn (VD: 100,000 dòng max) để tránh vòng lặp vô hạn
        if start >= 100000:
            break
            
    df = pd.DataFrame(all_data)
    if not df.empty:
        # Đổi tên cột cho chuẩn với hiển thị UI
        df = df.rename(columns={
            "ma_so_thue": "MST",
            "ten_cong_ty": "Tên công ty",
        })
        
        # Xử lý Map ID tỉnh thành
        if "tinh_thanh_id" in df.columns:
            def map_city(x):
                if str(x) == "1": return "Hà Nội"
                if str(x) == "2": return "Hồ Chí Minh"
                return str(x) if pd.notnull(x) else "Chưa xác định"
            df["Thành phố"] = df["tinh_thanh_id"].apply(map_city)
            
        # Bổ sung cột Ngành nghề (nếu Supabase chưa có) để UI không bị gãy
        if "Ngành nghề" not in df.columns:
            df["Ngành nghề"] = "Chưa phân loại"
            
    return df


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

    # 1. Upload file hoặc Tải từ Supabase
    col_up1, col_up2 = st.columns([1, 1])
    
    with col_up1:
        uploaded_file = st.file_uploader("Tải lên danh sách (CSV/Excel)", type=["csv", "xlsx"])
        
    with col_up2:
        st.write("Hoặc đồng bộ trực tiếp từ Database nội bộ")
        use_supabase = st.button("⬇️ Tải toàn bộ dữ liệu từ Supabase", type="primary", use_container_width=True)

    df = pd.DataFrame()
    
    if use_supabase:
        if not supabase:
            st.error("Chưa kết nối được Supabase. Vui lòng kiểm tra lại file .env")
            df = get_mock_data()
        else:
            with st.spinner("Đang kéo dữ liệu từ Supabase (quá trình này dùng Cache, lần sau sẽ rất nhanh)..."):
                df = fetch_all_enterprises_from_supabase()
            if not df.empty:
                st.success(f"✅ Đã tải thành công {len(df):,} doanh nghiệp từ Database!")
            else:
                st.warning("Bảng dữ liệu trong Supabase đang trống.")
                df = get_mock_data()
    elif uploaded_file is not None:
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
        st.info("Chưa có file nào được tải lên hoặc chọn đồng bộ. Đang hiển thị **dữ liệu mẫu (Mock Data)**.")

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
