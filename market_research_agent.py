import os
from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

# 1. Cấu hình API Key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError(
        "Thiếu GROQ_API_KEY. Hãy tạo file .env từ .env.example và điền key của bạn vào."
    )

from crewai import LLM
from crewai.tools import tool
from googlesearch import search

main_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)

@tool("internet_search_tool")
def search_tool(query: str) -> str:
    """Tìm kiếm thông tin trên Internet. Đầu vào là một chuỗi truy vấn tìm kiếm."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
            if not results:
                return "Không tìm thấy kết quả nào."
                
            output = []
            for r in results:
                output.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nLink: {r.get('href')}")
            return "\n\n".join(output)
    except Exception as e:
        return f"Lỗi tìm kiếm: {str(e)}"

# 2. Khởi tạo các Agents
researcher_agent = Agent(
    role="Market Researcher",
    goal=(
        "Tìm kiếm trên Internet và thu thập dữ liệu mới nhất, chính xác nhất về thị trường. "
        "TUYỆT ĐỐI KHÔNG tự bịa ra số liệu. Luôn dùng công cụ tìm kiếm để lấy dữ liệu thực tế."
    ),
    backstory=(
        "Bạn là một chuyên gia nghiên cứu thị trường xuất sắc. "
        "Bạn luôn sử dụng công cụ tìm kiếm trên mạng để tìm ra dữ liệu thật trước khi trả lời. "
        "Bạn không bao giờ đưa ra các con số ảo tưởng hay số liệu tự đoán."
    ),
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
    tools=[search_tool],
    max_iter=3
)

verifier_agent = Agent(
    role="Data Verifier",
    goal=(
        "Nhận dữ liệu thô từ Market Researcher, kiểm tra tính hợp lý, độ tin cậy. "
        "Loại bỏ các thông tin mâu thuẫn, sai lệch và đảm bảo số liệu chính xác tuyệt đối."
    ),
    backstory=(
        "Bạn là một chuyên gia kiểm định dữ liệu (Data QA) khắt khe. "
        "Bạn không chấp nhận những thông tin thiếu căn cứ hoặc số liệu không nhất quán. "
        "Nhiệm vụ của bạn là làm sạch dữ liệu trước khi nó được đưa vào báo cáo chính thức."
    ),
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
    max_iter=3
)

writer_agent = Agent(
    role="Report Writer",
    goal=(
        "Tổng hợp dữ liệu đã được kiểm duyệt từ Data Verifier và viết thành một báo cáo "
        "chuyên nghiệp, có cấu trúc rõ ràng (Tóm tắt, Phân tích chi tiết, Kết luận)."
    ),
    backstory=(
        "Bạn là một chuyên viên phân tích kinh doanh kiêm copywriter chuyên nghiệp. "
        "Bạn biết cách biến những số liệu khô khan thành một câu chuyện hấp dẫn, "
        "dễ hiểu và có tính thuyết phục cao dành cho ban giám đốc (C-level)."
    ),
    verbose=True,
    allow_delegation=False,
    llm=main_llm,
    max_iter=3
)

# 4. Định nghĩa luồng Nhiệm vụ (Tasks)
task1 = Task(
    description=(
        'Sử dụng công cụ tìm kiếm Internet để nghiên cứu toàn diện về chủ đề: "{topic}". '
        'Hãy thu thập dữ liệu chi tiết, các thống kê quan trọng, phân tích các xu hướng, '
        'và chỉ ra các cơ hội/thách thức (nếu có liên quan) đối với chủ đề này. '
        'BẮT BUỘC phải dùng search tool để lấy số liệu thực, không tự bịa.'
    ),
    expected_output=(
        "Một bản tóm tắt dữ liệu thô toàn diện về chủ đề được giao, "
        "bao gồm số liệu thực tế từ internet, xu hướng và nhận định chuyên gia."
    ),
    agent=researcher_agent,
)

task2 = Task(
    description=(
        "Đọc bản dữ liệu thô từ Task 1. Hãy kiểm tra logic, tìm các điểm mâu thuẫn hoặc "
        "những tuyên bố thiếu căn cứ. Đưa ra một bản dữ liệu đã được tinh chỉnh (cleaned data) "
        "chỉ giữ lại những thông tin đáng tin cậy."
    ),
    expected_output=(
        "Một danh sách các thông tin/số liệu đã được xác thực, loại bỏ các điểm phi lý."
    ),
    agent=verifier_agent,
)

task3 = Task(
    description=(
        "Sử dụng dữ liệu đã làm sạch từ Task 2, hãy viết một báo cáo phân tích hoàn chỉnh. "
        "Báo cáo phải được viết bằng tiếng Việt, định dạng Markdown chuyên nghiệp. "
        "Bắt buộc phải có các phần: Tóm tắt thực thi (Executive Summary), Phân tích chi tiết, và Kết luận/Khuyến nghị."
    ),
    expected_output=(
        "Một bài báo cáo định dạng Markdown, ngôn ngữ tiếng Việt chuyên nghiệp, sẵn sàng trình bày cho Ban Giám Đốc."
    ),
    agent=writer_agent,
)

def run_market_research(topic: str) -> str:
    # 5. Vận hành hệ thống
    market_research_crew = Crew(
        agents=[researcher_agent, verifier_agent, writer_agent],
        tasks=[task1, task2, task3],
        process=Process.sequential,
        verbose=True,
    )
    
    """Hàm này sẽ được gọi từ Streamlit UI."""
    result = market_research_crew.kickoff(inputs={"topic": topic})
    
    # CrewAI kickoff trả về đối tượng CrewOutput. Gọi thuộc tính raw để lấy string.
    if hasattr(result, 'raw'):
        return result.raw
    return str(result)

if __name__ == "__main__":
    test_topic = "Thị trường AI tại Việt Nam năm 2024"
    print(f"Khởi động hệ thống Market Research cho chủ đề: {test_topic}...\n")
    report = run_market_research(test_topic)

    print("\n" + "=" * 50)
    print(" BÁO CÁO NGHIÊN CỨU THỊ TRƯỜNG ĐÃ HOÀN THÀNH:")
    print("=" * 50)
    print(report)
