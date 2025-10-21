import logging
import pandas as pd
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from rapidfuzz import process, fuzz

# ===== إعدادات عامة =====
TOKEN = "8474192793:AAE_WDC4q-NUwD9cnP8-zokydFgrlB4wI6w"
ADMIN_IDS = [7592972606]
CHANNEL_LINK = "https://t.me/orwateck"
CONTACT_LINK = "https://t.me/orwatech1"
EXCEL_PATH = "قائمة الشاشات.xlsx"

# ===== إعداد السجل =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== تحميل ملف التوافقات =====
df = pd.read_excel(EXCEL_PATH)

# ===== تجهيز قائمة البحث مسبقًا =====
search_list = [(i, re.sub(r'\s+|[^A-Za-z0-9]', '', str(row["الشركة"]) + str(row["الأجهزة المتوافقة"])).upper())
               for i, row in df.iterrows()]

# ===== لوحة الأزرار الرئيسية =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("🔍 بحث عن توافق", callback_data="search")],
        [InlineKeyboardButton("👑 حول المطور", callback_data="about")],
        [
            InlineKeyboardButton("📡 قناتي الرئيسية", url=CHANNEL_LINK),
            InlineKeyboardButton("💬 راسلني", url=CONTACT_LINK),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== تنظيف النص للبحث =====
def normalize_text(text):
    text = re.sub(r'\s+', '', str(text))
    text = re.sub(r'[^A-Za-z0-9]', '', text)
    return text.upper()

# ===== رسالة البداية =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = f"""
🎬 <b>أهلاً وسهلاً {user.first_name}</b> 👋  
✨ أنا بوت <b>ORWA TECH - عروة تيك</b> لمطابقة الشاشات والأجهزة ✨  

📱 أرسل موديل الجهاز الذي تريد البحث عنه .. مثال " X9A " 👇
"""
    if update.message:
        await update.message.reply_html(welcome_text, reply_markup=main_menu())
    else:
        await update.callback_query.message.reply_html(welcome_text, reply_markup=main_menu())

# ===== البحث الذكي مع اقتراح أقرب موديلات =====
async def search_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = normalize_text(update.message.text)
    responses = []

    # البحث المباشر أولاً
    for i, text in search_list:
        if query in text:
            company = df.loc[i, "الشركة"]
            original_devices = df.loc[i, "الأجهزة المتوافقة"]
            responses.append(f"🏷️ <b>{company}</b>\n📱 {original_devices}")

    if responses:
        response_text = "\n\n".join(responses)
    else:
        # البحث عن أفضل 3 اقتراحات بسرعة
        suggestions = process.extract(query, [t[1] for t in search_list], scorer=fuzz.token_sort_ratio, limit=3)
        suggestion_text = "\n".join([
            f"🔹 {df.loc[search_list[i][0], 'الشركة']} {df.loc[search_list[i][0], 'الأجهزة المتوافقة']}" 
            for i, s, score in suggestions if score > 50
        ])
        if suggestion_text:
            response_text = f"❌ لم يتم العثور على توافق مباشر. أقرب النتائج:\n{suggestion_text}"
        else:
            response_text = f"❌ لم يتم العثور على توافقات للموديل أو الشركة: <b>{update.message.text}</b>"

    await update.message.reply_html(response_text, reply_markup=main_menu())

# ===== الأزرار =====
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await query.message.reply_text("🧠 أرسل الآن موديل الجهاز أو اسم الشركة للبحث 🔍")
    elif query.data == "about":
        about_text = """
👑 <b>المطور:</b> عروة خالد دوابشة  
🧰 <b>الاختصاص:</b> صيانة وبرمجة الموبايلات  
⚙️ <b>النسخة:</b> 1.0  
📡 <b>بوت التوافقات الذكي</b>
"""
        await query.message.reply_html(about_text, reply_markup=main_menu())

# ===== أوامر المشرف =====
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("🚫 أنت لست مسؤولاً عن هذا البوت.")
        return

    try:
        new_admin = int(context.args[0])
        if new_admin not in ADMIN_IDS:
            ADMIN_IDS.append(new_admin)
            await update.message.reply_text(f"✅ تمت إضافة {new_admin} كمسؤول جديد.")
        else:
            await update.message.reply_text("ℹ️ هذا المستخدم مضاف مسبقاً.")
    except:
        await update.message.reply_text("⚠️ استخدم الأمر هكذا:\n/addadmin <USER_ID>")

# ===== تشغيل البوت =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_model))

    print("✅ البوت يعمل الآن...")
    app.run_polling()
