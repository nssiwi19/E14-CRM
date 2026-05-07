import streamlit as st
from market_research_agent import run_market_research
from crm_b2b_agent import run_b2b_crm

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Market Insights & CRM", page_icon="📈", layout="wide")

# --- CUSTOM CSS ---
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
st.markdown('<h1 class="gradient-text">📈 AI Market Insights & CRM</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Hệ thống Trợ lý AI (Powered by CrewAI & Groq Llama-3).</p>', unsafe_allow_html=True)

# --- KHỞI TẠO SESSION STATE (Lịch sử Chat) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR (Điều khiển) ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    if st.button("🧹 Xóa Lịch sử Trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- STREAMLIT TABS ---
tab1, tab2 = st.tabs(["📊 Market Research", "🤝 CRM B2B Response"])

with tab1:
    st.markdown("### 🕵️‍♂️ Nghiên cứu thị trường")
    # --- HIỂN THỊ LỊCH SỬ CHAT ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- XỬ LÝ NHẬP LIỆU (CHAT INPUT) ---
    if prompt := st.chat_input("VD: Doanh nghiệp nào của Việt Nam nộp thuế nhiều nhất 2025?"):
        # 1. Hiển thị câu hỏi của User
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 2. Xử lý câu trả lời của Assistant
        with st.chat_message("assistant"):
            with st.status(f"Đang phân tích sâu về: **{prompt}**", expanded=True) as status:
                st.write("🕵️‍♂️ **Market Researcher** đang thu thập số liệu...")
                st.write("🔍 **Data Verifier** đang kiểm chứng...")
                st.write("✍️ **Report Writer** đang tổng hợp báo cáo...")
                
                try:
                    report = run_market_research(prompt)
                    status.update(label="✅ Phân tích hoàn tất!", state="complete", expanded=False)
                    st.markdown(report)
                    st.session_state.messages.append({"role": "assistant", "content": report})
                except Exception as e:
                    error_msg = f"❌ Đã xảy ra lỗi: {str(e)}"
                    status.update(label="Lỗi xử lý", state="error", expanded=True)
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

with tab2:
    st.markdown("### 📩 Xử lý Email Đối tác B2B")
    st.markdown("Dán email từ khách hàng/đối tác vào đây để AI phân tích ý định và tự động tra cứu thông tin CRM tương ứng.")
    
    email_input = st.text_area("Nhập nội dung email từ đối tác:", height=200, placeholder="Ví dụ: Tôi là Tuấn từ Công ty Cổ phần Bán lẻ Minh Tuấn (MST: 0314456789)...")
    
    if st.button("🚀 Phân tích & Tạo phản hồi", type="primary"):
        if email_input.strip():
            with st.status("Đang xử lý yêu cầu...", expanded=True) as status:
                st.write("🤖 **Classifier Agent** đang phân tích Intent & bóc tách thực thể...")
                st.write("🔍 **Data Agent** đang tra cứu thông tin doanh nghiệp trong CRM...")
                st.write("✍️ **Response Agent** đang soạn thảo email phản hồi thấu cảm...")
                
                try:
                    b2b_response = run_b2b_crm(email_input)
                    status.update(label="✅ Xử lý hoàn tất!", state="complete", expanded=False)
                    st.markdown("### 📝 Bản nháp Email phản hồi:")
                    st.markdown(b2b_response)
                except Exception as e:
                    status.update(label="Lỗi xử lý", state="error", expanded=True)
                    st.error(f"❌ Đã xảy ra lỗi: {str(e)}")
        else:
            st.warning("Vui lòng nhập nội dung email trước khi gửi.")
