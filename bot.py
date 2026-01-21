import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os

# On récupère les clés depuis les "Secrets" (Variables d'environnement)
TOKEN = os.getenv('TOKEN_TELEGRAM')
API_KEY = os.getenv('API_FOOTBALL_KEY')
HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

logging.basicConfig(level=logging.INFO)

# --- STOCKAGE TEMPORAIRE (Parlay) ---
user_parlays = {} # Pour garder en mémoire tes 4 matchs

# --- LOGIQUE API ---
def get_matches(league_id=None):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": datetime.now().strftime("%Y-%m-%d")}
    if league_id: params["league"] = league_id
    if league_id == 2: params["season"] = 2025 # UCL
    
    resp = requests.get(url, headers=HEADERS, params=params).json()
    return resp.get("response", [])

# --- INTERFACE TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏆 Champions League", callback_data='league_2')],
        [InlineKeyboardButton("🇫🇷 Ligue 1", callback_data='league_61')],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League", callback_data='league_39')],
        [InlineKeyboardButton("📂 Autres Catégories", callback_data='categories')],
        [InlineKeyboardButton("📝 Mon Parlay (0/4)", callback_data='view_parlay')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "⚽ *FLASH ANALYSIS BOT*\n\nBienvenue ! Choisis une ligue pour analyser tes 4 matchs."
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith('league_'):
        l_id = data.split('_')[1]
        matches = get_matches(l_id)
        if not matches:
            await query.edit_message_text("⚠️ Aucun match trouvé pour cette ligue aujourd'hui.", 
                                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Retour", callback_data='back')]]))
            return

        keyboard = []
        for m in matches[:8]: # Limite à 8 pour l'écran
            txt = f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}"
            keyboard.append([InlineKeyboardButton(txt, callback_data=f"analyze_{m['fixture']['id']}")])
        
        keyboard.append([InlineKeyboardButton("↩️ Menu Principal", callback_data='back')])
        await query.edit_message_text("🔍 Sélectionne un match à analyser :", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'back':
        await start(update, context)

# --- LANCEMENT ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    print("🚀 Le bot est prêt sur Telegram !")
    app.run_polling()
