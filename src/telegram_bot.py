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
import pandas as pd

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

# Function to create a fixed menu
def get_fixed_menu():
    return [
        [InlineKeyboardButton("شروع مجدد", callback_data='restart')],
        [InlineKeyboardButton("منو اصلی", callback_data='main_menu')],
        [InlineKeyboardButton("پایان مکالمه", callback_data='end_conversation')],
    ]

# Create a function to handle manual input
async def handle_manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['manual_input'] = True
    await update.message.reply_text("لطفاً اطلاعات خود را وارد کنید. هر بخش را با خط جدید جدا کنید.")
    await update.message.reply_text("برای مثال: 'فروش: 1000000'")

# Function to handle text input (manual data entry)
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user = update.effective_user

    if context.user_data.get('manual_input', False):
        context.user_data['manual_data'] = user_message  # Store the user's input
        
        # Confirm receipt of manual input and ask for the next step
        await update.message.reply_text("اطلاعات شما ثبت شد. در حال پردازش...")
        await update.message.reply_text("لطفاً نوع تحلیل را انتخاب کنید:", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("سود و زیان", callback_data='analyze_profit')],
            [InlineKeyboardButton("آیتم‌های پرفروش", callback_data='analyze_sales')],
            [InlineKeyboardButton("آیتم‌های پرمصرف", callback_data='analyze_usage')],
        ]))
        
        # Change manual input flag to false to avoid further manual entries
        context.user_data['manual_input'] = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_parts = [
        f"سلام {user.first_name}! 👋",
        "من **CaReMa** هستم. دستیار هوشمند مالی کافه و رستوران. 💼",
        "میتونم باهات گپ بزنم، فایلاتو تحلیل کنم و مشاوره بدم!",
        "از منوی زیر شروع کن یا هر سوالی داری همینجا بپرس. 😊"
    ]
    for part in welcome_parts:
        await update.message.reply_text(part)

    keyboard = [
        [InlineKeyboardButton("📤 بارگذاری اطلاعات", callback_data='upload_data')],
        [InlineKeyboardButton("📊 تحلیل اطلاعات", callback_data='analyze_data')],
        [InlineKeyboardButton("📜 بازبینی اطلاعات گذشته", callback_data='review_data')],
    ]
    # Add the fixed menu
    keyboard.extend(get_fixed_menu())

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("منوی اصلی 👇", reply_markup=reply_markup)

# Function to handle the button callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'upload_data':
        keyboard = [
            [InlineKeyboardButton("دستورالعمل‌های مصرف مواد", callback_data='upload_usage')],
            [InlineKeyboardButton("فاکتورهای خرید", callback_data='upload_purchase')],
            [InlineKeyboardButton("فاکتورهای فروش", callback_data='upload_sales')],
            [InlineKeyboardButton("هدررفت و دورریز", callback_data='upload_waste')],
            [InlineKeyboardButton("هزینه‌های ماهانه", callback_data='upload_expenses')],
            [InlineKeyboardButton("وارد کردن دستی", callback_data='manual_input')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً دسته‌بندی فایل یا داده‌ها را انتخاب کنید:", reply_markup=reply_markup)

    elif query.data == 'manual_input':
        # Trigger manual data input flow
        await handle_manual_input(update, context)

    elif query.data == 'analyze_data':
        keyboard = [
            [InlineKeyboardButton("سود و زیان", callback_data='analyze_profit')],
            [InlineKeyboardButton("آیتم‌های پرفروش و کم‌فروش", callback_data='analyze_sales')],
            [InlineKeyboardButton("آیتم‌های پرمصرف و بهینه", callback_data='analyze_usage')],
            [InlineKeyboardButton("پیشنهاد قیمت‌گذاری", callback_data='analyze_pricing')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً نوع تحلیل رو انتخاب کن:", reply_markup=reply_markup)

    elif query.data == 'restart':
        await start(update, context)  # Restart the bot conversation
    
    elif query.data == 'main_menu':
        # Send back to the main menu
        await query.message.reply_text("این هم منو اصلی. لطفاً یکی از گزینه‌ها رو انتخاب کن:")
        await start(update, context)  # Send the main menu again
    
    elif query.data == 'end_conversation':
        await query.message.reply_text("پایان مکالمه. اگر دوباره نیاز به کمک داشتی، من اینجام! 😊")

# Handle received documents
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

def main():
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    app.run_polling()

if __name__ == '__main__':
    main()
