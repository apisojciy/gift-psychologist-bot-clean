from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters

YOUR_USERNAME = "andriy_pisotskiy"

PSYCHOLOGISTS = [
    ("Ткаченко Юлія Леонідівна", "https://doc.ua/ua/doctor/kiev/22001-yuliya-tkachenko/about"),
    ("Ольга Сергієнко", "https://k-s.org.ua/branches/team/olga-sergiyenko/"),
    ("Шкварок Наталія Борисівна", "https://uccbt.com.ua/specialists/shkvarok-nataliya-borysivna/")
]

user_choices = {}

async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Готова розпочати", callback_data='start_course')]]
    await update.message.reply_text("Привіт! 🎁 Це подарунок – 5 сеансів у психолога.", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "start_course":
        keyboard = [
            [InlineKeyboardButton(name, url=url, callback_data=f"choose_{i}")] for i, (name, url) in enumerate(PSYCHOLOGISTS)
        ]
        keyboard.append([InlineKeyboardButton("Інший психолог", callback_data="choose_other")])
        await query.message.reply_text("Оберіть психолога:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("choose_"):
        user_id = query.from_user.id
        if query.data == "choose_other":
            await query.message.reply_text("Введіть ім’я та посилання на психолога:")
            user_choices[user_id] = 'awaiting_custom_input'
        else:
            index = int(query.data.split("_")[1])
            name, url = PSYCHOLOGISTS[index]
            await notify_user(context, name, url, user_id)
            await query.message.reply_text("Дякую! Очікуйте на інформацію :)")

async def notify_user(context: CallbackContext, name, url, user_id):
    message = f"👤 Дівчина вибрала психолога:\n{name}\n{url}"
    await context.bot.send_message(chat_id=f"@{YOUR_USERNAME}", text=message)
    user_choices[user_id] = None

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_choices.get(user_id) == 'awaiting_custom_input':
        await notify_user(context, update.message.text, "-", user_id)
        await update.message.reply_text("Дякую! Очікуйте на інформацію :)")

def main():
    TOKEN = "7588127606:AAGscvK5SeIdZ3Qsx_oNzR4cK0A6njFD9mM"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == '__main__':
    main()