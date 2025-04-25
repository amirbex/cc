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
        # شروع مکالمه با مدل Gemini
        chat = model.start_chat()
        
        # ارسال پیام به مدل برای دریافت تحلیل
        response = chat.send_message(prompt)
        
        # بازگشت متن پاسخ از مدل
        return response.text
    
    except Exception as e:
        # مدیریت خطاهای احتمالی
        return f"خطا در اتصال به API جمینای: {str(e)}"

def chat_with_gemini(message: str) -> str:
    """Send a message to Gemini and get the response."""
    # تنظیم API key از محیط
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    
    # مدل پیشرفته‌ی Gemini
    model = genai.GenerativeModel('gemini-1.5-pro')

    try:
        # شروع مکالمه با مدل Gemini
        chat = model.start_chat()
        
        # ارسال پیام به مدل برای دریافت پاسخ
        response = chat.send_message(message)
        
        # بازگشت متن پاسخ از مدل
        return response.text
    
    except Exception as e:
        # مدیریت خطاهای احتمالی
        return f"خطا در اتصال به API جمینای: {str(e)}"
