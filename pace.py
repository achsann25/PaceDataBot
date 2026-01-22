import gspread
import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import datetime

# --- CONFIGURATION ---
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
SHEET_NAME = 'PaceDataBot' 
JSON_FILE = 'creds.json'
AUTHORIZED_USER_ID =int(os.getenv('USER_ID'))

# --- CONNECT TO GOOGLE SHEETS ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(JSON_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# --- UTILITY FUNCTIONS ---
# Fungsi ini WAJIB ada di atas sebelum dipanggil oleh start/handle_message
async def is_authorized(update: Update):
    user_id = update.effective_user.id
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("⛔ Akses Ditolak. Bot ini hanya untuk penggunaan pribadi achsan.")
        return False
    return True

# 1. Perintah /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    welcome_msg = (
        "🏃‍♂️ **Selamat Datang di Jogging Tracker buatan achsan!**\n\n"
        "Gunakan bot ini untuk mencatat progress lari Anda.\n\n"
        "📍 **Format Input:**\n"
        "`Jarak, Waktu, Pace, HR`\n\n"
        "💡 **Contoh:**\n"
        "`5.0, 25:30, 05:06, 165`\n\n"
        "🗑️ **Hapus Data:**\n"
        "Ketik /hapus untuk menghapus input terakhir."
    )
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# 2. Perintah /hapus
async def hapus_terakhir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    try:
        all_rows = sheet.get_all_values()
        last_row_index = len(all_rows)
        if last_row_index <= 1:
            await update.message.reply_text("❌ Tidak ada data untuk dihapus.")
            return

        last_data = all_rows[-1]
        sheet.delete_rows(last_row_index)
        await update.message.reply_text(
            f"🗑️ **Data Berhasil Dihapus!**\n\n"
            f"Data lari {last_data[1]} km pada tanggal {last_data[0]} telah dihapus.",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Gagal menghapus: {e}")

# 3. Handler Input Data
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return
    user_text = update.message.text
    try:
        parts = [item.strip() for item in user_text.split(',')]
        if len(parts) != 4:
            await update.message.reply_text("⚠️ Format salah! Gunakan: `Jarak, Waktu, Pace, HR`", parse_mode='Markdown')
            return

        jarak = float(parts[0].replace(',', '.'))
        hr = int(parts[3])
        waktu = parts[1]
        pace = parts[2]
        tanggal = datetime.date.today().strftime("%Y-%m-%d")
        row = [tanggal, jarak, waktu, pace, hr]
        sheet.append_row(row)
        
        await update.message.reply_text(
            f"✅ **DATA TERSIMPAN!**\n\n"
            f"📅 Tanggal: {tanggal}\n"
            f"🏁 Jarak: {jarak} km\n"
            f"⏱️ Waktu: {waktu}\n"
            f"⚡ Pace: {pace}\n"
            f"❤️ Heart Rate: {hr} bpm",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text("❌ **Input Tidak Valid!**\nPastikan Jarak dan HR berupa angka.", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan: {e}")

# --- MAIN RUNNER ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hapus", hapus_terakhir))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚀 Bot Jogging Aktif!")
    app.run_polling()