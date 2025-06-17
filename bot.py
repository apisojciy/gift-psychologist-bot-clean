from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters

YOUR_USERNAME = "andriy_pisotskiy" # Впевнись, що це саме ім'я користувача, а не ID. Для надсилання повідомлень за ID краще використовувати chat_id.

PSYCHOLOGISTS = [
    ("Ткаченко Юлія Леонідівна", "https://doc.ua/ua/doctor/kiev/22001-yuliya-tkachenko/about"),
    ("Ольга Сергієнко", "https://k-s.org.ua/branches/team/olga-sergiyenko/"),
    ("Шкварок Наталія Борисівна", "https://uccbt.com.ua/specialists/shkvarok-nataliya-borysivna/")
]

user_choices = {} # Використовуватиметься для відстеження стану користувача

async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Готова розпочати", callback_data='start_course')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message: # Перевірка, чи є об'єкт message
        await update.message.reply_text("Привіт! 🎁 Це подарунок – 5 сеансів у психолога.", reply_markup=reply_markup)
    else: # Це може статися, якщо команда /start викликана не через нове повідомлення (наприклад, після перезапуску бота)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Привіт! 🎁 Це подарунок – 5 сеансів у психолога.", reply_markup=reply_markup)


async def handle_choice(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer() # Обов'язково відповідаємо на callback_query, щоб прибрати "годинник" з кнопки

    if query.data == "start_course":
        keyboard_buttons = []
        for i, (name, url) in enumerate(PSYCHOLOGISTS):
            # Важливо: callback_data для кнопок з URL не передається. URL відкривається безпосередньо.
            # Якщо ви хочете, щоб кнопка була інтерактивною (і виконувала callback_data),
            # але при цьому мала URL, це складніше. Зазвичай, або URL, або callback_data.
            # Тут я припускаю, що ви хочете, щоб при натисканні на ім'я психолога відкривався URL.
            # Тому callback_data тут не використовується для кнопок з URL.
            # Якщо ви хочете відстежувати вибір психолога, то URL потрібно виводити окремо.
            keyboard_buttons.append([InlineKeyboardButton(name, url=url)]) # Кнопка з URL

        # Додаємо кнопки для відстеження вибору психолога, якщо це потрібно окремо
        # Якщо ви хочете, щоб при натисканні на ім'я психолога *також* відстежувався вибір,
        # вам потрібно зробити дві кнопки або змінити логіку.
        # Наприклад, ось так (якщо URL не є основною дією, а є інформацією):
        keyboard_choice_tracking = [
            [InlineKeyboardButton(name, callback_data=f"choose_psychologist_{i}")] for i, (name, url) in enumerate(PSYCHOLOGISTS)
        ]
        # І потім виводити URL як частину тексту
        # await query.edit_message_text(f"Оберіть психолога: \n{PSYCHOLOGISTS[0][0]} - {PSYCHOLOGISTS[0][1]}", reply_markup=InlineKeyboardMarkup(keyboard_choice_tracking))

        # Оскільки у вас в original code була callback_data у кнопках з URL, я її відновлюю, але пам'ятайте
        # що callback_data не "працює" на кнопках з URL - URL відкривається.
        # Можливо, ви хотіли щоб URL був у тексті, а callback_data була для обробки вибору.
        keyboard = [[InlineKeyboardButton(name, url=url, callback_data=f"choose_{i}")] for i, (name, url) in enumerate(PSYCHOLOGISTS)]
        keyboard.append([InlineKeyboardButton("Інший психолог", callback_data="choose_other")])

        await query.edit_message_text("Оберіть психолога:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("choose_"):
        user_id = query.from_user.id
        if query.data == "choose_other":
            await query.message.reply_text("Введіть ім’я та посилання на психолога:")
            user_choices[user_id] = 'awaiting_custom_input'
        else:
            index = int(query.data.split("_")[1])
            name, url = PSYCHOLOGISTS[index]
            await notify_admin(context, name, url, user_id) # Змінено назву функції на notify_admin
            await query.message.reply_text("Дякую! Очікуйте на інформацію :)")

# Перейменовано для ясності, що функція повідомляє адміна
async def notify_admin(context: CallbackContext, name: str, url: str, user_id: int):
    # YOUR_USERNAME має бути ID чату або ім'ям групи/каналу, куди відсилається повідомлення.
    # Якщо це ім'я користувача, то він має написати боту першим, і бот повинен знати його chat_id.
    # Краще використовувати chat_id адміністратора, якщо він відомий.
    # Якщо YOUR_USERNAME - це chat_id користувача Андрія, то все добре.
    # Якщо це username, то потрібно отримати його chat_id.
    # Наприклад, ви можете створити окрему команду для адміна, щоб він повідомив боту свій ID.
    message = f"👤 Дівчина (ID: {user_id}) вибрала психолога:\nІм'я: {name}\nПосилання: {url}"
    try:
        # Важливо: Якщо YOUR_USERNAME - це просто ім'я, а не chat_id, це може не працювати.
        # Краще зберігати chat_id адміністратора.
        await context.bot.send_message(chat_id=f"@{YOUR_USERNAME}", text=message)
    except Exception as e:
        print(f"Помилка відправки повідомлення адміну {YOUR_USERNAME}: {e}")
        # Можна відправити повідомлення користувачу про помилку, або логувати її.
    user_choices[user_id] = None # Скидаємо стан користувача після обробки

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_choices.get(user_id) == 'awaiting_custom_input':
        # Якщо користувач вводить ім'я та посилання в одному повідомленні,
        # вам потрібно розпарсити update.message.text.
        # Наразі, ваш код приймає все повідомлення як ім'я, а посилання ставиться як "-".
        # Можливо, краще запросити окремо ім'я, потім посилання.
        custom_input = update.message.text.strip()
        # Простий варіант: припустимо, користувач вводить "Ім'я Психолога, Посилання"
        if ',' in custom_input:
            name, url = custom_input.split(',', 1) # Розділити лише за першою комою
            name = name.strip()
            url = url.strip()
        else: # Якщо користувач просто ввів ім'я без посилання
            name = custom_input
            url = "Посилання не надано" # Або попросіть ввести посилання окремо

        await notify_admin(context, name, url, user_id) # Змінено назву функції
        await update.message.reply_text("Дякую! Очікуйте на інформацію :)")
        # Після обробки вводу, скидаємо стан
        user_choices[user_id] = None

def main():
    TOKEN = "7588127606:AAGscvK5SeIdZ3Qsx_oNzR4cK0A6njFD9mM"
    # Для нових версій python-telegram-bot використовується ApplicationBuilder
    app = ApplicationBuilder().token(TOKEN).build()

    # Додавання обробників залишається схожим
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_choice))
    # MessageHandler для текстових повідомлень, які не є командами
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота. run_polling() тепер метод об'єкта Application
    print("Бот запущено. Очікування оновлень...")
    app.run_polling()

if __name__ == '__main__':
    main()
