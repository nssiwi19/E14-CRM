import ast
import os
import re
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.tools import tool
from dotenv import load_dotenv

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
    Truy vấn cơ sở dữ liệu 100k doanh nghiệp bằng Mã số thuế (MST) hoặc Tên công ty.
    Trả về thông tin chi tiết: MST, Tên, Năm thành lập, Ngành nghề kinh doanh, Địa chỉ.
    """
    # Mock data mô phỏng Database chứa 100k bản ghi doanh nghiệp tại HN & HCM
    mock_db = {
        "0101248141": {
            "MST": "0101248141",
            "Tên công ty": "Công ty TNHH Phần mềm Công nghệ FPT",
            "Năm thành lập": "2000",
            "Địa chỉ": "Quận Cầu Giấy, Hà Nội",
            "Ngành nghề kinh doanh": "Sản xuất phần mềm và Dịch vụ CNTT",
            "Trạng thái CRM": "Khách hàng VIP, đang gia hạn gói Cloud",
        },
        "0314456789": {
            "MST": "0314456789",
            "Tên công ty": "Công ty Cổ phần Bán lẻ Minh Tuấn",
            "Năm thành lập": "2017",
            "Địa chỉ": "Quận 1, TP. Hồ Chí Minh",
            "Ngành nghề kinh doanh": "Bán lẻ thiết bị điện tử",
            "Trạng thái CRM": "Đối tác mới, đang gặp khó khăn tích hợp API thanh toán",
        },
    }

    query = (mst_or_name or "").strip()
    if not query:
        return "Không tìm thấy dữ liệu doanh nghiệp trong hệ thống CRM."

    # Tìm kiếm theo MST
    if query in mock_db:
        return str(mock_db[query])

    # Tìm kiếm theo tên (giả lập)
    for data in mock_db.values():
        if query.lower() in data["Tên công ty"].lower():
            return str(data)

    return "Không tìm thấy dữ liệu doanh nghiệp trong hệ thống CRM."


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
    role="Empathetic B2B Communications Specialist",
    goal=(
        "Viết email phản hồi đối tác dựa trên dữ liệu CRM được cung cấp. "
        "Cần áp dụng Empathetic Response Generation (ERG) để tạo sự thấu hiểu."
    ),
    backstory=(
        "Bạn là giám đốc quan hệ khách hàng. Bạn hiểu rằng phía sau mỗi doanh nghiệp là những con người. "
        "Bạn luôn dùng thông tin ngành nghề và vị trí địa lý để tạo ra sự kết nối, đồng cảm với khó khăn kỹ thuật "
        "của họ, giữ văn phong chuyên nghiệp nhưng ấm áp."
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
        "Sử dụng dữ liệu trả về từ Task 2 và email gốc, hãy soạn một email tiếng Việt phản hồi. "
        "Đồng cảm với đặc thù ngành bán lẻ (lỗi thanh toán tại quầy là rất nghiêm trọng), "
        "đưa kế hoạch xử lý ưu tiên, và cá nhân hóa theo trạng thái CRM."
    ),
    expected_output=(
        "Một email tiếng Việt hoàn chỉnh, chuyên nghiệp, thể hiện rõ sự thấu hiểu (ERG) "
        "và cá nhân hóa theo thông tin doanh nghiệp."
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
