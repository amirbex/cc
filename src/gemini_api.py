import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def analyze_with_gemini(data, category):
    """Send data to Gemini API for analysis."""
    # تنظیم API key از محیط
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    # مدل پیشرفته‌ی Gemini
    model = genai.GenerativeModel('gemini-1.5-pro')

    # ایجاد prompt برای تحلیل داده‌ها
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
        # ارسال درخواست به مدل و دریافت پاسخ
        chat = model.start_chat()
        response = chat.send_message(prompt)
        
        # بازگشت متن پاسخ
        return response.text
    
    except Exception as e:
        # مدیریت خطاهای احتمالی
        return f"خطا در اتصال به API جمینای: {str(e)}"
