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
from src.gemini_api import analyze_with_gemini
from src.visualization import plot_sales

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message and main menu."""
    user = update.effective_user
    welcome_message = (
        f"سلام {user.first_name}! 😊 من **CaReMa**، دستیار هوشمند مدیریت کافه و رستوران، نسخه حسابداری‌ام!\n"
        "اسمم مخفف Cafe Restaurant Managerه، و این نسخه‌ام مخصوص تحلیل داده‌های مالی کافه‌ته. 💼\n"
        "می‌تونم فاکتورهای خرید، فروش، هدررفت، و هزینه‌ها رو برات تحلیل کنم و نمودارهای قشنگ نشونت بدم.\n"
        "آماده‌ای کافه‌ت رو به سطح بعدی ببری؟ 🚀 از منوی زیر شروع کن!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📤 بارگذاری اطلاعات", callback_data='upload_data')],
        [InlineKeyboardButton("📊 تحلیل اطلاعات", callback_data='analyze_data')],
        [InlineKeyboardButton("📜 بازبینی اطلاعات گذشته", callback_data='review_data')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == 'upload_data':
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
    """Handle uploaded Excel files."""
    document = update.message.document
    if not document.file_name.endswith('.xlsx'):
        await update.message.reply_text("لطفاً فقط فایل اکسل (.xlsx) آپلود کنید!")
        return

    category = context.user_data.get('category')
    if not category:
        await update.message.reply_text("لطفاً اول دسته‌بندی رو از منو انتخاب کن!")
        return

    # Send thinking message
    thinking_message = await update.message.reply_text("در حال فکر کردن هستم... 🧠")

    # Download file
    file = await document.get_file()
    file_path = f'temp_data/{document.file_name}'
    os.makedirs('temp_data', exist_ok=True)
    await file.download_to_drive(file_path)

    # Process data
    try:
        data = load_excel_data(file_path)
        validate_excel_structure(data, category)
    except ValueError as e:
        await update.message.reply_text(str(e))
        await thinking_message.delete()
        os.remove(file_path)
        return

    # Analyze with Gemini
    analysis_result = analyze_with_gemini(data, category)

    # Generate visualization (only for sales in this version)
    visualizations = []
    if category == 'فروش':
        viz_path = f'results/visualizations/{document.file_name}_sales.png'
        visualizations.append(plot_sales(data, viz_path))

    # Save analysis
    os.makedirs('results/analysis_reports', exist_ok=True)
    analysis_path = f'results/analysis_reports/{category}_{document.file_name}.txt'
    with open(analysis_path, 'w', encoding='utf-8') as f:
        f.write(analysis_result)

    # Delete thinking message
    await thinking_message.delete()

    # Send results
    await update.message.reply_text(analysis_result)
    for viz_path in visualizations:
        with open(viz_path, 'rb') as viz_file:
            await update.message.reply_photo(viz_file, caption=f"نمودار {category} - {document.file_name}")
        os.remove(viz_path)

    # Cleanup
    os.remove(file_path)
    await update.message.reply_text("می‌خوای تحلیل دیگه‌ای انجام بدم یا فایل جدید آپلود کنی؟ 😄")

def main():
    """Run the Telegram bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    app.run_polling()

if __name__ == '__main__':
    main()
