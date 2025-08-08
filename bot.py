import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes, CallbackQueryHandler
import os
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ASK_GENDER, ASK_AGE, ASK_HEIGHT, ASK_WEIGHT, ASK_WAIST = range(5)

token = os.getenv("bot_token")

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Erkak", callback_data='erkak'),
         InlineKeyboardButton("Ayol", callback_data='ayol')]
    ]
    await update.message.reply_text(
        "👋 *Salom!* Men *Fitly* — sog‘lomlik ko‘rsatkichlari bo‘yicha yordamchingizman.\n\n"
        "Avval jinsingizni tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ASK_GENDER

# --- GENDER (INLINE BUTTON) ---
async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = query.data
    context.user_data['gender'] = gender
    await query.edit_message_text("🧍 Yoshingiz nechada?")
    return ASK_AGE

# --- AGE ---
async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text)
        if age < 5 or age > 120:
            raise ValueError
        context.user_data['age'] = age
        await update.message.reply_text("📏 Bo‘yingiz (sm) nechada?")
        return ASK_HEIGHT
    except:
        await update.message.reply_text("❗ Iltimos, yoshingizni to‘g‘ri kiriting (5-120).")
        return ASK_AGE

# --- HEIGHT ---
async def ask_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        height = float(update.message.text)
        if height < 50 or height > 250:
            raise ValueError
        context.user_data['height'] = height
        await update.message.reply_text("⚖️ Vazningiz (kg) nechada?")
        return ASK_WEIGHT
    except:
        await update.message.reply_text("❗ Iltimos, bo‘yingizni to‘g‘ri kiriting (50-250 sm).")
        return ASK_HEIGHT

# --- WEIGHT ---
async def ask_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text)
        if weight < 20 or weight > 300:
            raise ValueError
        context.user_data['weight'] = weight
        await update.message.reply_text("📐 Bel o‘lchamingiz (sm) nechada?")
        return ASK_WAIST
    except:
        await update.message.reply_text("❗ Iltimos, vazningizni to‘g‘ri kiriting (20-300 kg).")
        return ASK_WEIGHT

# --- CALCULATE ---
async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        waist = float(update.message.text)
        if waist < 30 or waist > 200:
            raise ValueError
        context.user_data['waist'] = waist

        gender = context.user_data['gender']
        age = context.user_data['age']
        height = context.user_data['height']
        weight = context.user_data['weight']

        height_m = height / 100
        bmi = weight / (height_m ** 2)
        if gender == "erkak":
            bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
            ibw = 50 + 0.9 * (height - 152)
        else:
            bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
            ibw = 45.5 + 0.9 * (height - 152)
        tdee = bmr * 1.55
        bf = (1.20 * bmi) + (0.23 * age) - (10.8 if gender == "erkak" else 0) - 5.4

        # Yakuniy xulosa matn ko‘rinishida
        summary = (
            f"**Sizning sog‘lomlik ko‘rsatkichlaringiz:**\n\n"
            f"• **BMI:** {bmi:.1f} — {'Normal' if 18.5 <= bmi < 25 else 'Me’yordan tashqari'}\n"
            f"• **BMR:** {bmr:.0f} kcal (bazal almashinuv)\n"
            f"• **TDEE:** {tdee:.0f} kcal (kunlik energiya sarfi)\n"
            f"• **BF:** {bf:.1f}% (tana yog‘i foizi)\n"
            f"• **Ideal vazn:** {ibw:.1f} kg\n\n"
            f"_Tavsiyalar: Sog‘lom ovqatlaning va muntazam jismoniy faollikni saqlang._"
        )

        await update.message.reply_text(summary, parse_mode="Markdown")
        return ConversationHandler.END

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Xatolik yuz berdi. Qayta urinib ko‘ring.")
        return ConversationHandler.END

# --- CANCEL ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hisoblash bekor qilindi.")
    return ConversationHandler.END

# --- MAIN ---
def main():
    
    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_GENDER: [CallbackQueryHandler(ask_gender)],
            ASK_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_age)],
            ASK_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_height)],
            ASK_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_weight)],
            ASK_WAIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, calculate)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == '__main__':
    main()
