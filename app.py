import streamlit as st
import google.generativeai as genai
import os
import json

# Load API Key từ Secrets của Streamlit Cloud
genai.configure(api_key=st.secrets["GEMINI"]["API_KEY"])

# Prompt cho Gemini
SYSTEM_PROMPT = """
Bạn là Chuyên gia Phân tích Cuộc gọi CSKH. 
Phân tích transcript hoặc audio và trả về đúng định dạng JSON sau, không thêm bất kỳ chữ nào khác:
{
  "total_score": 85,
  "criteria_scores": {"1": 9, "2": 8, "3": 9, "4": 7, "5": 10, "6": 8, "7": 6, "8": 9},
  "strengths": ["Điểm mạnh 1", "Điểm mạnh 2"],
  "weaknesses": ["Điểm yếu"],
  "improvement_suggestions": ["Góp ý cải thiện 1", "Góp ý cải thiện 2"],
  "recommended_script_snippet": "Câu nói gợi ý thay thế"
}
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",     # hoặc "gemini-2.5-flash-latest"
    system_instruction=SYSTEM_PROMPT
)

st.title("🤖 Chatbot Phân Tích Cuộc Gọi CSKH")
st.caption("Upload file ghi âm (.mp3, .wav) hoặc transcript (.txt)")

uploaded_file = st.file_uploader("Chọn file cuộc gọi", 
                                 type=["mp3", "wav", "ogg", "m4a", "txt"])

if uploaded_file and st.button("🚀 Phân tích cuộc gọi"):
    with st.spinner("Gemini đang phân tích cuộc gọi... (có thể mất 15-40 giây với file audio)"):
        try:
            if uploaded_file.type.startswith("audio"):
                # Sửa lỗi mime type bằng cách chỉ định rõ ràng
                mime_type = uploaded_file.type  # ví dụ: audio/wav, audio/mpeg...
                if not mime_type:
                    mime_type = "audio/wav"   # fallback nếu không detect được
                
                # Upload với mime_type rõ ràng
                uploaded_gemini = genai.upload_file(
                    uploaded_file, 
                    mime_type=mime_type
                )
                response = model.generate_content([uploaded_gemini, "Hãy phân tích chất lượng cuộc gọi chăm sóc khách hàng này một cách chi tiết."])
            
            else:
                # Với file text (.txt)
                text = uploaded_file.read().decode("utf-8")
                response = model.generate_content(text)

            # Parse kết quả JSON
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            result = json.loads(result_text)

            st.success(f"Điểm tổng thể: **{result.get('total_score', 0)}/100** ⭐")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Điểm theo tiêu chí")

                criteria_names = {
                    "1": "1. Chào hỏi & Giới thiệu",
                    "2": "2. Lắng nghe & Thấu hiểu khách hàng",
                    "3": "3. Xác nhận vấn đề & Hỏi câu hỏi hiệu quả",
                    "4": "4. Giải pháp & Kiến thức sản phẩm",
                    "5": "5. Thái độ & Giọng điệu",
                    "6": "6. Tuân thủ kịch bản công ty",
                    "7": "7. Xử lý từ chối / Khách khó tính",
                    "8": "8. Kết thúc cuộc gọi & Call-to-Action"
                }

                for k, v in result.get("criteria_scores", {}).items():
                    name = criteria_names.get(k, f"Tiêu chí {k}")
                    st.write(f"**{name}**")
                    st.progress(v / 10)
                    st.caption(f"Điểm: {v}/10")
                    st.markdown("---")

            with col2:
                st.subheader("Điểm mạnh")
                for s in result.get("strengths", []):
                    st.write("✅", s)
            st.subheader("💡 Góp ý cải thiện cho nhân viên")
            for sugg in result.get("improvement_suggestions", []):
                st.write("→", sugg)

            if "recommended_script_snippet" in result:
                st.subheader("Câu nói gợi ý thay thế")
                st.code(result["recommended_script_snippet"], language="markdown")

        except Exception as e:
            st.error(f"Đã có lỗi: {str(e)}")
