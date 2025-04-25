import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def analyze_with_gemini(data, category):
    """Send data to Gemini API for analysis."""
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-1.5-pro')

    prompt = f"""
    داده‌های زیر مربوط به یک کافه در دسته‌بندی '{category}' است:
    {data}
    لطفاً تحلیل جامعی به فارسی ارائه دهید، شامل:
    - روندهای کلیدی (مثلاً پرفروش‌ترین محصولات یا پرهزینه‌ترین موارد)
    - پیشنهادات برای بهبود (مثلاً کاهش هدررفت یا افزایش فروش)
    - هر گونه ناهنجاری (مثلاً هزینه‌های غیرعادی)
    پاسخ ساختارمند و کاربرپسند باشد.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"خطا در اتصال به API جمینای: {str(e)}"
