import ast
import os
import re
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from dotenv import load_dotenv

try:
    from database import supabase
except ImportError:
    supabase = None

# 1. Cấu hình API Key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError(
        "Thiếu GROQ_API_KEY hợp lệ. Hãy tạo file .env từ .env.example hoặc set biến môi trường."
    )

main_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)


# 2. Định nghĩa công cụ truy xuất dữ liệu doanh nghiệp (Tool Calling)
@tool("search_enterprise_database")
def search_enterprise_database(mst_or_name: str) -> str:
    """
    Truy vấn cơ sở dữ liệu doanh nghiệp từ Supabase bằng Mã số thuế (MST) hoặc Tên công ty.
    Trả về thông tin chi tiết: MST, Tên, Năm thành lập, SĐT, Email, Địa chỉ.
    """
    query = (mst_or_name or "").strip()
    if not query:
        return "Không tìm thấy dữ liệu doanh nghiệp do truy vấn rỗng."

    if not supabase:
        return "Lỗi: Không thể kết nối đến cơ sở dữ liệu Supabase (Client chưa được khởi tạo). Hãy kiểm tra file .env"

    table_name = "doanh_nghiep"  # CHÚ Ý: Đổi tên này nếu bảng trong Supabase của bạn tên khác
    
    try:
        # Nếu query có vẻ là MST (có số, độ dài >= 10)
        if any(char.isdigit() for char in query) and len(query) >= 10:
            response = supabase.table(table_name).select("ma_so_thue, ten_cong_ty, nam_thanh_lap, so_dien_thoai, email, dia_chi, tinh_thanh_id").eq("ma_so_thue", query).execute()
        else:
            # Tìm gần đúng theo tên công ty (không phân biệt hoa thường)
            response = supabase.table(table_name).select("ma_so_thue, ten_cong_ty, nam_thanh_lap, so_dien_thoai, email, dia_chi, tinh_thanh_id").ilike("ten_cong_ty", f"%{query}%").execute()
            
        def _map_tinh_thanh(record):
            # Ánh xạ ID Tỉnh thành sang tên để AI hiểu
            tt_id = record.get("tinh_thanh_id")
            if tt_id == 1 or tt_id == "1":
                record["Ten_Tinh_Thanh"] = "Hà Nội"
            elif tt_id == 2 or tt_id == "2":
                record["Ten_Tinh_Thanh"] = "TP. Hồ Chí Minh"
            return record

        data = response.data
        if data and len(data) > 0:
            # Trả về string JSON bản ghi đầu tiên tìm được để Agent có thể đọc
            return str(_map_tinh_thanh(data[0]))
            
        # Fallback: Nếu không tìm thấy, thử tìm lại với ilike cho tên công ty
        response_fallback = supabase.table(table_name).select("ma_so_thue, ten_cong_ty, nam_thanh_lap, so_dien_thoai, email, dia_chi, tinh_thanh_id").ilike("ten_cong_ty", f"%{query}%").execute()
        if response_fallback.data and len(response_fallback.data) > 0:
            return str(_map_tinh_thanh(response_fallback.data[0]))
            
        return f"Không tìm thấy dữ liệu doanh nghiệp nào khớp với '{query}' trong hệ thống CRM."
    except Exception as e:
        return f"Lỗi truy vấn cơ sở dữ liệu Supabase: {str(e)}"


def _extract_mst_or_company_name(task1_output: str) -> Optional[str]:
    """
    Heuristic fallback để bóc tách MST/Tên công ty từ kết quả Task 1,
    giúp Task 2 gọi tool ổn định hơn trong demo.
    """
    if not task1_output:
        return None

    mst_match = re.search(r"\b\d{10,14}\b", task1_output)
    if mst_match:
        return mst_match.group(0)

    company_match = re.search(
        r"(Công ty[^.,\n]+)",
        task1_output,
        flags=re.IGNORECASE,
    )
    if company_match:
        return company_match.group(1).strip()
    return None


# 3. Khởi tạo các Agents
classifier_agent = Agent(
    role="B2B Intent & Entity Classifier",
    goal=(
        "Đọc văn bản, phân loại mục đích liên hệ của đối tác và trích xuất "
        "Mã số thuế (MST) hoặc Tên công ty một cách chính xác nhất."
    ),
    backstory=(
        "Bạn là chuyên gia phân tích dữ liệu văn bản B2B. Bạn luôn bóc tách các thực thể "
        "như MST (dãy số) hoặc Tên công ty để hệ thống phía sau tra cứu."
    ),
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
)

data_agent = Agent(
    role="Enterprise Data Analyst",
    goal=(
        "Sử dụng MST hoặc Tên công ty từ Agent trước để tra cứu thông tin doanh nghiệp "
        "trong cơ sở dữ liệu bằng công cụ search_enterprise_database."
    ),
    backstory=(
        "Bạn là người nắm giữ quyền truy cập kho dữ liệu 100.000 doanh nghiệp Việt Nam. "
        "Bạn luôn lấy thông tin gốc từ cơ sở dữ liệu thay vì tự bịa ra."
    ),
    tools=[search_enterprise_database],
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
)

response_agent = Agent(
    role="Chuyên viên Hỗ trợ Đối tác của Esgoo CRM",
    goal=(
        "Viết email phản hồi B2B chuyên nghiệp để trả lời khiếu nại của đối tác. "
        "Tuyệt đối không được nhầm lẫn vai trò: Bạn là nhân viên của Esgoo CRM, và bạn đang trả lời khách hàng."
    ),
    backstory=(
        "Bạn là Chuyên viên Hỗ trợ Đối tác (Partner Support Specialist) tại công ty nền tảng phần mềm Esgoo CRM. "
        "Khách hàng của bạn là các công ty/doanh nghiệp khác (B2B) đang sử dụng API hoặc phần mềm của Esgoo. "
        "Mỗi khi họ gửi email báo lỗi, bạn sẽ kiểm tra thông tin công ty họ trong Database, sau đó viết email trả lời "
        "để trấn an và đưa ra hướng xử lý. Bạn luôn làm việc chuyên nghiệp, thấu hiểu, và luôn ký tên là 'Đội ngũ hỗ trợ kỹ thuật - Esgoo CRM'."
    ),
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
)


# 4. Định nghĩa luồng Nhiệm vụ (Tasks)
task1 = Task(
    description=(
        'Phân tích email sau: "{enterprise_email}". '
        "Hãy xác định vấn đề họ đang gặp phải, phân loại intent "
        "(Hợp tác/Hỗ trợ/Khiếu nại) và trích xuất Mã số thuế hoặc Tên công ty."
    ),
    expected_output=(
        "Một JSON string gồm 3 khóa: intent, issue_summary, entity. "
        "Ví dụ: {'intent':'Hỗ trợ','issue_summary':'...','entity':'0314456789'}"
    ),
    agent=classifier_agent,
)

task2 = Task(
    description=(
        "Lấy entity từ kết quả Task 1 và truyền vào công cụ search_enterprise_database "
        "để truy vấn dữ liệu CRM. Nếu output không chuẩn JSON, tự bóc tách MST/Tên công ty."
    ),
    expected_output=(
        "Dữ liệu chi tiết của doanh nghiệp (MST, Ngành nghề, Địa chỉ, Trạng thái...) "
        "được lấy từ Database."
    ),
    agent=data_agent,
)

task3 = Task(
    description=(
        "Đọc email khiếu nại gốc của đối tác, và đọc dữ liệu công ty của họ do Task 2 vừa lấy từ Database (ví dụ: Tên công ty, Ngành nghề...). "
        "Nhiệm vụ: Viết MỘT (1) email phản hồi hoàn chỉnh để gửi lại cho người đó.\n\n"
        "QUY TẮC NGHIÊM NGẶT (PHẢI TUÂN THỦ 100%):\n"
        "1. VAI TRÒ: Bạn đại diện cho 'Esgoo CRM'. Tuyệt đối KHÔNG nhận bạn là người của công ty khách hàng.\n"
        "2. NGƯỜI NHẬN: Gửi đích danh tới người gửi email hoặc Kính gửi đại diện của [Tên công ty khách hàng lấy từ Task 2].\n"
        "3. LỖI ĐIỀN KHUYẾT: CẤM SỬ DỤNG các ngoặc vuông như [Tên của bạn], [Chức danh], [Số điện thoại]. Nếu cần, hãy tự xưng là 'Tuấn Anh - Quản lý Hỗ trợ Kỹ thuật Esgoo' và số điện thoại ảo của Esgoo.\n"
        "4. NỘI DUNG: Áp dụng sự thấu cảm dựa trên đúng ngành nghề của công ty đó (ví dụ truyền thông thì lo về KPI, bán lẻ thì lo thanh toán). Trình bày lộ trình xử lý lỗi rõ ràng 3 bước."
    ),
    expected_output=(
        "Một bức email B2B hoàn chỉnh bằng tiếng Việt, sẵn sàng để gửi đi ngay lập tức mà không cần con người chỉnh sửa lại. "
        "Kết thúc bằng chữ ký của Đội ngũ hỗ trợ Esgoo CRM."
    ),
    agent=response_agent,
)

def run_b2b_crm(email_content: str) -> str:
    # 5. Vận hành hệ thống
    b2b_crm_crew = Crew(
        agents=[classifier_agent, data_agent, response_agent],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=True,
    )
    
    result = b2b_crm_crew.kickoff(inputs={"enterprise_email": email_content})
    
    if hasattr(result, 'raw'):
        return result.raw
    return str(result)


if __name__ == "__main__":
    test_email = """
    Kính gửi đội ngũ hỗ trợ,
    Tôi là Tuấn từ Công ty Cổ phần Bán lẻ Minh Tuấn (MST: 0314456789).
    Hiện tại hệ thống cửa hàng của chúng tôi đang bị lỗi khi gọi API đối soát dữ liệu với nền tảng của các bạn.
    Lỗi này đang ảnh hưởng trực tiếp đến việc thanh toán của khách hàng tại quầy. Mong các bạn kiểm tra gấp.
    """
    
    print("Khởi động hệ thống Auto-Classification & Response CRM...\n")
    result = run_b2b_crm(test_email)

    print("\n" + "=" * 50)
    print(" EMAIL PHẢN HỒI ĐÃ ĐƯỢC TẠO TỰ ĐỘNG:")
    print("=" * 50)
    print(result)
