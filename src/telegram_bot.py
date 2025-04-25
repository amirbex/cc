import os
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
from dotenv import load_dotenv
from data_processing import load_excel_data, validate_excel_structure, parse_manual_data
from gemini_api import analyze_with_gemini, chat_with_gemini
from visualization import plot_sales

load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')

# Fixed menu

def get_fixed_menu():
    return [
        [InlineKeyboardButton("شروع مجدد", callback_data='restart')],
        [InlineKeyboardButton("منو اصلی", callback_data='main_menu')],
        [InlineKeyboardButton("پایان مکالمه", callback_data='end_conversation')],
    ]

# Handle /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome = [
        f"سلام {user.first_name}! 👋",
        "من CaReMa هستم؛ دستیار هوشمند مالی کافه و رستوران ☕",
        "میتونم باهات گپ بزنم، فایلاتو تحلیل کنم و مشاوره بدم.",
    ]
    for part in welcome:
        await update.message.reply_text(part)

    keyboard = [
        [InlineKeyboardButton("📤 بارگذاری اطلاعات", callback_data='upload_data')],
        [InlineKeyboardButton("📊 تحلیل اطلاعات", callback_data='analyze_data')],
        [InlineKeyboardButton("📜 بازبینی اطلاعات گذشته", callback_data='review_data')],
    ]
    keyboard.extend(get_fixed_menu())
    await update.message.reply_text("منوی اصلی 👇", reply_markup=InlineKeyboardMarkup(keyboard))

# Manual data input
async def handle_manual_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['manual_input'] = True
    await update.message.reply_text("لطفاً اطلاعات خود را وارد کنید (مثلاً:\nفروش: 1000000\nهزینه: 500000)")

# Receive and parse text input
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('manual_input'):
        manual_text = update.message.text
        try:
            data = parse_manual_data(manual_text)
            context.user_data['parsed_manual_data'] = data
            await update.message.reply_text("اطلاعات دریافت شد. در حال تحلیل... 🧠")

            result = analyze_with_gemini(data, "manual")

            for part in result.split("\n\n"):
                await update.message.reply_text(part)

        except Exception as e:
            await update.message.reply_text(f"خطا در پردازش اطلاعات: {e}")

        context.user_data['manual_input'] = False

# Document upload
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith('.xlsx'):
        await update.message.reply_text("فقط فایل اکسل (.xlsx) مجاز است.")
        return

    category = context.user_data.get('category', 'generic')
    thinking_msg = await update.message.reply_text("در حال فکر کردن هستم... 🧠")

    file = await document.get_file()
    os.makedirs('temp_data', exist_ok=True)
    path = f'temp_data/{document.file_name}'
    await file.download_to_drive(path)

    try:
        data = load_excel_data(path)
        if category != 'generic':
            validate_excel_structure(data, category)
        result = analyze_with_gemini(data, category)

        await thinking_msg.delete()
        for part in result.split("\n\n"):
            await update.message.reply_text(part)

        if category == 'فروش':
            plot_path = f'results/visualizations/{document.file_name}_sales.png'
            img = plot_sales(data, plot_path)
            with open(img, 'rb') as f:
                await update.message.reply_photo(f)
            os.remove(img)

    except Exception as e:
        await update.message.reply_text(str(e))
        await thinking_msg.delete()
    finally:
        os.remove(path)

# Button callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'upload_data':
        kb = [
            [InlineKeyboardButton("📎 فایل اکسل", callback_data='upload_excel')],
            [InlineKeyboardButton("✍️ وارد کردن دستی", callback_data='manual_input')],
        ]
        await query.message.reply_text("یکی از روش‌های ورود اطلاعات را انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'upload_excel':
        context.user_data['category'] = 'generic'
        await query.message.reply_text("فایل خود را ارسال کنید (فرمت: .xlsx)")

    elif query.data == 'manual_input':
        await handle_manual_input(update, context)

    elif query.data == 'analyze_data':
        kb = [
            [InlineKeyboardButton("سود و زیان", callback_data='analyze_profit')],
            [InlineKeyboardButton("آیتم‌های پرفروش", callback_data='analyze_sales')],
            [InlineKeyboardButton("آیتم‌های پرمصرف", callback_data='analyze_usage')],
            [InlineKeyboardButton("پیشنهاد قیمت‌گذاری", callback_data='analyze_pricing')],
        ]
        await query.message.reply_text("لطفاً نوع تحلیل را انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb))

    elif query.data == 'restart':
        await start(update, context)

    elif query.data == 'main_menu':
        await start(update, context)

    elif query.data == 'end_conversation':
        await query.message.reply_text("مکالمه پایان یافت. هر وقت خواستی دوباره صدام کن! 😊")

# Main entry

def main():
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    app.run_polling()

if __name__ == '__main__':
    main()
