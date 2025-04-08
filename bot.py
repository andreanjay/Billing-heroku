import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
HEROKU_API_KEY = os.getenv("HEROKU_API_KEY")
HEROKU_API_URL = "https://api.heroku.com/apps"
HEADERS = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}"
}

def to_wib(timestamp):
    dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(hours=7)
    return dt.strftime("%d-%m-%Y %H:%M WIB")

async def cekheroku(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sedang mengambil data aplikasi Heroku kamu...")

    try:
        res = requests.get(HEROKU_API_URL, headers=HEADERS)
        if res.status_code != 200:
            await update.message.reply_text(f"Error {res.status_code}:
{res.text}")
            return

        apps = res.json()
        if not apps:
            await update.message.reply_text("Kamu belum punya aplikasi Heroku.")
            return

        msg = "📋 *Daftar Aplikasi Heroku:*

"
        for app in apps:
            msg += f"• `{app['name']}`
"
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Terjadi error:
{str(e)}")

async def hapusapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Format: /hapusapp nama_aplikasi")
        return

    app_name = context.args[0]
    keyboard = [[InlineKeyboardButton("Ya, hapus", callback_data=f"hapus_{app_name}"),
                 InlineKeyboardButton("Batal", callback_data="batal")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Yakin ingin menghapus app `{app_name}`?", reply_markup=reply_markup, parse_mode="Markdown")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("hapus_"):
        app_name = data.split("_", 1)[1]
        res = requests.delete(f"{HEROKU_API_URL}/{app_name}", headers=HEADERS)
        if res.status_code == 202:
            await query.edit_message_text(f"✅ App `{app_name}` berhasil dihapus.", parse_mode="Markdown")
        else:
            await query.edit_message_text(f"Gagal hapus app:
{res.text}")
    elif data == "batal":
        await query.edit_message_text("Penghapusan dibatalkan.")

async def statusapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Format: /statusapp nama_aplikasi")
        return

    app_name = context.args[0]
    try:
        res = requests.get(f"{HEROKU_API_URL}/{app_name}", headers=HEADERS)
        if res.status_code != 200:
            await update.message.reply_text(f"Error {res.status_code}:
{res.text}")
            return

        app = res.json()
        created = to_wib(app['created_at'])
        region = app.get('region', {}).get('name', '-')
        stack = app.get('stack', {}).get('name', '-')

        msg = f"""• *{app_name}*
• Region: {region}
• Stack: {stack}
• Dibuat: {created}
• Status: Aktif"""
        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Terjadi error:
{str(e)}")

async def statusall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Lagi ngecek status semua aplikasi Heroku...")

    try:
        res = requests.get(HEROKU_API_URL, headers=HEADERS)
        if res.status_code != 200:
            await update.message.reply_text(f"Error {res.status_code}:
{res.text}")
            return

        apps = res.json()
        if not apps:
            await update.message.reply_text("Kamu belum punya aplikasi Heroku.")
            return

        msg = "📋 *Status Semua App Heroku:*

"
        for app in apps:
            name = app['name']
            created = to_wib(app['created_at'])
            region = app.get('region', {}).get('name', '-')
            stack = app.get('stack', {}).get('name', '-')

            msg += (
                f"• {name}
"
                f"   Region: {region} | Stack: {stack}
"
                f"   Dibuat: {created}
"
                f"   Status: Aktif

"
            )

        await update.message.reply_text(msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"Terjadi error:
{str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """
╭─〔 *Heroku Bot Command* 〕
├ /cekheroku — Liat semua app kamu di Heroku
├ /hapusapp nama_app — Hapus app (dengan tombol confirm)
├ /statusapp nama_app — Liat status & info detail app
├ /statusall — Liat status semua aplikasi kamu
├ /help — Ya ini... help.

Contoh:
/hapusapp autobotku
/statusapp userbotku
"""
    await update.message.reply_text(msg, parse_mode="Markdown")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("cekheroku", cekheroku))
app.add_handler(CommandHandler("hapusapp", hapusapp))
app.add_handler(CommandHandler("statusapp", statusapp))
app.add_handler(CommandHandler("statusall", statusall))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(handle_callback))
app.run_polling()
