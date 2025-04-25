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
        [InlineKeyboardButton("شروع مجدد", callback_data='restart')],
        [InlineKeyboardButton("منو اصلی", callback_data='main_menu')],
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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'upload_data':
        keyboard = [
            [InlineKeyboardButton("بارگذاری اکسل", callback_data='upload_excel')],
            [InlineKeyboardButton("وارد کردن دستی", callback_data='manual_input')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text("لطفاً یکی از روش‌های بارگذاری را انتخاب کن:", reply_markup=reply_markup)

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

    elif query.data == 'manual_input':
        await query.message.reply_text("لطفاً اطلاعات کافه یا رستوران خود را به صورت متنی وارد کن. اطلاعات مورد نظر شامل مواردی مانند فروش روزانه، هزینه‌ها، و آیتم‌های پرفروش است.")

        # Set the flag that user is now entering manual data
        context.user_data['manual_input'] = True

    elif query.data == 'upload_excel':
        await query.message.reply_text("لطفاً فایل اکسل خود را آپلود کن.")

    elif query.data == 'restart':
        await start(update, context)  # Restart the bot conversation
    
    elif query.data == 'main_menu':
        await query.message.reply_text("این هم منو اصلی. لطفاً یکی از گزینه‌ها رو انتخاب کن:")
        await start(update, context)  # Send the main menu again
    
    elif query.data == 'end_conversation':
        await query.message.reply_text("پایان مکالمه. اگر دوباره نیاز به کمک داشتی، من اینجام! 😊")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    if context.user_data.get('manual_input'):
        # Handle manual input data
        await update.message.reply_text("در حال پردازش اطلاعات شما... 🧠")
        
        # تحلیل داده‌ها و ارسال جواب به طور مرحله به مرحله
        analysis_result = analyze_with_gemini(user_message, "داده‌های وارد شده")

        # ارسال تحلیل به صورت روان
        for part in analysis_result.split("\n"):
            await update.message.reply_text(part)
        
        # بعد از تحلیل، سوالات اضافی برای تکمیل تحلیل پرسیده شود
        await update.message.reply_text("آیا سوال دیگری دارید؟ یا می‌خواهید اطلاعات جدید وارد کنید؟ 😊")
        
        # Clear the manual input flag
        context.user_data['manual_input'] = False

    else:
        # Handle normal chat with Gemini
        response = chat_with_gemini(user_message)
        await update.message.reply_text(response)

        os.makedirs('results/conversations', exist_ok=True)
        with open('results/conversations/log.txt', 'a', encoding='utf-8') as f:
            f.write(f"User: {user_message}\nBot: {response}\n\n")

def main():
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()
