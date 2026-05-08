import os
from database import supabase
from crm_b2b_agent import search_enterprise_database

def test_supabase_integration():
    print("="*50)
    print("🚀 BẮT ĐẦU TEST KẾT NỐI SUPABASE")
    print("="*50)

    # 1. Kiểm tra Client
    if not supabase:
        print("❌ LỖI: Supabase client chưa được khởi tạo. Vui lòng kiểm tra file .env có chứa SUPABASE_URL và SUPABASE_KEY chưa.")
        return
    
    print("✅ 1. Khởi tạo Supabase client thành công.")
    
    # 2. Kiểm tra truy vấn trực tiếp
    table_name = "doanh_nghiep"
    print(f"\n🔍 2. Đang thử đọc dữ liệu từ bảng '{table_name}'...")
    
    try:
        # Lấy thử 1 bản ghi bất kỳ
        response = supabase.table(table_name).select("ma_so_thue, ten_cong_ty").limit(1).execute()
        
        if response.data and len(response.data) > 0:
            sample_record = response.data[0]
            print(f"✅ Đọc dữ liệu thành công! Bản ghi mẫu: {sample_record}")
            
            # 3. Kiểm tra Tool của Agent
            test_mst = sample_record.get("ma_so_thue")
            if test_mst:
                print(f"\n🤖 3. Đang test Tool 'search_enterprise_database' của Agent với MST: {test_mst}...")
                
                # Vì đây là Tool của CrewAI (được bọc bởi @tool), ta không gọi như hàm bình thường được
                # Thử gọi qua .func (nếu có) hoặc .run()
                if hasattr(search_enterprise_database, 'func'):
                    agent_result = search_enterprise_database.func(test_mst)
                elif hasattr(search_enterprise_database, '_run'):
                    agent_result = search_enterprise_database._run(test_mst)
                else:
                    # Truyền theo dạng kwargs nếu run() yêu cầu
                    agent_result = search_enterprise_database.run({"mst_or_name": test_mst})

                
                print("✅ Kết quả trả về từ Tool:")
                print("-" * 30)
                print(agent_result)
                print("-" * 30)
        else:
            print(f"⚠️ Bảng '{table_name}' tồn tại nhưng hiện đang trống (0 bản ghi).")
            print("👉 Vui lòng thêm dữ liệu vào bảng để test Tool của Agent.")
            
    except Exception as e:
        print(f"❌ LỖI KHI TRUY VẤN: {e}")
        print(f"👉 Vui lòng kiểm tra:")
        print(f"  1. Tên bảng '{table_name}' có đúng không?")
        print(f"  2. Quyền RLS (Row Level Security) có đang chặn không (vì bạn dùng anon key)?")

if __name__ == "__main__":
    test_supabase_integration()
