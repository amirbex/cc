import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
from data_processing import load_excel_data, validate_excel_structure
from gemini_api import analyze_with_gemini, chat_with_gemini
from visualization import plot_sales

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

# Function to create a fixed menu
def get_fixed_menu():
    return [
        [InlineKeyboardButton("شروع", callback_data='start_conversation')],
        [InlineKeyboardButton("پایان مکالمه", callback_data='end_conversation')],
    ]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_parts = [
        f"سلام {user.first_name}! 👋",
        "من **CaReMa** هستم. دستیار هوشمند مالی کافه و رستوران. 💼",
        "میتونم باهات گپ بزنم، فایلاتو تحلیل کنم و مشاوره بدم!",
        "از منوی زیر شروع کن یا هر سوالی داری همینجا بپرس. 😊"
    ]
    
    # استفاده از update.effective_message برای ارسال پیام
    for part in welcome_parts:
        if update.effective_message:
            await update.effective_message.reply_text(part)

    # منوی اصلی
    keyboard = [
        [InlineKeyboardButton("📤 بارگذاری اطلاعات", callback_data='upload_data')],
        [InlineKeyboardButton("📊 تحلیل اطلاعات", callback_data='analyze_data')],
        [InlineKeyboardButton("📜 بازبینی اطلاعات گذشته", callback_data='review_data')],
    ]
    keyboard.extend(get_fixed_menu())  # افزودن منوی ثابت به کیبورد
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.effective_message:
        await update.effective_message.reply_text("منوی اصلی 👇", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'start_conversation':
        # نمایش منوی اصلی بعد از شروع مکالمه
        await start(update, context)

    elif query.data == 'end_conversation':
        # بازگشت به منوی اصلی بعد از پایان مکالمه
        await query.message.reply_text("پایان مکالمه. اگر دوباره نیاز به کمک داشتی، من اینجام! 😊")
        await start(update, context)  # نمایش مجدد منوی اصلی

    elif query.data == 'upload_data':
        keyboard = [
            [InlineKeyboardButton("دستورالعمل‌های مصرف مواد", callback_data='upload_usage')],
            [InlineKeyboardButton("فاکتورهای خرید", callback_data='upload_purchase')],
            [InlineKeyboardButton("فاکتورهای فروش", callback_data='upload_sales')],
            [InlineKeyboardButton("هدررفت و دورریز", callback_data='upload_waste')],
            [InlineKeyboardButton("هزینه‌های ماهانه", callback_data='upload_expenses')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً دسته‌بندی فایل اکسل رو انتخاب کن:", reply_markup=reply_markup)

    elif query.data == 'analyze_data':
        keyboard = [
            [InlineKeyboardButton("سود و زیان", callback_data='analyze_profit')],
            [InlineKeyboardButton("آیتم‌های پرفروش و کم‌فروش", callback_data='analyze_sales')],
            [InlineKeyboardButton("آیتم‌های پرمصرف و بهینه", callback_data='analyze_usage')],
            [InlineKeyboardButton("پیشنهاد قیمت‌گذاری", callback_data='analyze_pricing')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً نوع تحلیل رو انتخاب کن:", reply_markup=reply_markup)

    elif query.data == 'review_data':
        keyboard = [
            [InlineKeyboardButton("فروش کلی آیتم‌ها", callback_data='review_total_sales')],
            [InlineKeyboardButton("فروش طبقه‌بندی‌شده", callback_data='review_categorized_sales')],
            [InlineKeyboardButton("فروش خارج از چارچوب", callback_data='review_anomalous_sales')],
            [InlineKeyboardButton("درآمدهای جانبی", callback_data='review_other_income')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً نوع داده‌های گذشته رو انتخاب کن:", reply_markup=reply_markup)

    elif query.data.startswith('upload_'):
        category_map = {
            'upload_usage': 'دستورالعمل‌های مصرف مواد',
            'upload_purchase': 'خرید',
            'upload_sales': 'فروش',
            'upload_waste': 'هدررفت',
            'upload_expenses': 'هزینه‌ها'
        }
        category = category_map[query.data]
        context.user_data['category'] = category
        await query.message.reply_text(f"لطفاً فایل اکسل برای '{category}' رو آپلود کن.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.xlsx'):
        await update.message.reply_text("لطفاً فقط فایل اکسل (.xlsx) آپلود کنید!")
        return

    category = context.user_data.get('category')
    if not category:
        await update.message.reply_text("لطفاً اول دسته‌بندی رو از منو انتخاب کن!")
        return

    thinking_message = await update.message.reply_text("در حال فکر کردن هستم... 🧠")

    file = await document.get_file()
    file_path = f'temp_data/{document.file_name}'
    os.makedirs('temp_data', exist_ok=True)
    await file.download_to_drive(file_path)

    try:
        data = load_excel_data(file_path)
        validate_excel_structure(data, category)
    except ValueError as e:
        await update.message.reply_text(str(e))
        await thinking_message.delete()
        os.remove(file_path)
        return

    analysis_result = analyze_with_gemini(data, category)

    visualizations = []
    if category == 'فروش':
        viz_path = f'results/visualizations/{document.file_name}_sales.png'
        visualizations.append(plot_sales(data, viz_path))

    os.makedirs('results/analysis_reports', exist_ok=True)
    analysis_path = f'results/analysis_reports/{category}_{document.file_name}.txt'
    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write(analysis_result)

    await thinking_message.delete()

    await update.message.reply_text(analysis_result)
    for viz_path in visualizations:
        with open(viz_path, 'rb') as viz_file:
            await update.message.reply_photo(viz_file, caption=f"نمودار {category} - {document.file_name}")
        os.remove(viz_path)

    os.remove(file_path)
    await update.message.reply_text("می‌خوای تحلیل دیگه‌ای انجام بدم یا فایل جدید آپلود کنی؟ 😄")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    response = chat_with_gemini(user_message)
    await update.message.reply_text(response)

    os.makedirs('results/conversations', exist_ok=True)
    with open('results/conversations/log.txt', 'a', encoding='utf-8') as f:
        f.write(f"User: {user_message}\nBot: {response}\n\n")

def main():
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
