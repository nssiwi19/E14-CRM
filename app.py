import streamlit as st
from market_research_agent import run_market_research

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Market Insights", page_icon="📈", layout="wide")

# --- CUSTOM CSS (Chỉ giữ lại Gradient Text, bỏ các nền gây lỗi) ---
st.markdown("""
<style>
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 0px !important;
        padding-bottom: 10px;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #8B949E;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<h1 class="gradient-text">📈 AI Market Insights</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Trợ lý Nghiên cứu Thị trường Tự động (Powered by CrewAI & Groq Llama-3).</p>', unsafe_allow_html=True)

# --- KHỞI TẠO SESSION STATE (Lịch sử Chat) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR (Điều khiển) ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    if st.button("🧹 Xóa Lịch sử Trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.markdown("**Luồng làm việc của Agent:**")
    st.markdown("1. 🕵️‍♂️ **Market Researcher**\n   Thu thập dữ liệu thô.")
    st.markdown("2. 🔍 **Data Verifier**\n   Làm sạch và kiểm chứng.")
    st.markdown("3. ✍️ **Report Writer**\n   Viết báo cáo chuyên nghiệp.")

# --- HIỂN THỊ LỊCH SỬ CHAT ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- XỬ LÝ NHẬP LIỆU (CHAT INPUT) ---
if prompt := st.chat_input("VD: Doanh nghiệp nào của Việt Nam nộp thuế nhiều nhất 2025?"):
    # 1. Hiển thị câu hỏi của User
    with st.chat_message("user"):
        st.markdown(prompt)
    # Lưu vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Xử lý câu trả lời của Assistant
    with st.chat_message("assistant"):
        # Hiển thị thanh trạng thái đang làm việc
        with st.status(f"Đang phân tích sâu về: **{prompt}**", expanded=True) as status:
            st.write("🕵️‍♂️ **Market Researcher** đang thu thập số liệu...")
            st.write("🔍 **Data Verifier** đang kiểm tra tính xác thực...")
            st.write("✍️ **Report Writer** đang tổng hợp báo cáo Markdown...")
            
            try:
                # Gọi hệ thống CrewAI
                report = run_market_research(prompt)
                status.update(label="✅ Phân tích hoàn tất!", state="complete", expanded=False)
                
                # Hiển thị báo cáo
                st.markdown(report)
                
                # Lưu vào lịch sử
                st.session_state.messages.append({"role": "assistant", "content": report})
            except Exception as e:
                error_msg = f"❌ Đã xảy ra lỗi: {str(e)}"
                status.update(label="Lỗi xử lý", state="error", expanded=True)
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
