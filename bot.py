import os
import time
import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove

# ==================== МОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8964975943:AAGn_sPgDWCUni140MGJNYxVAyqOwHNWM-8"

# Настройки Monobank (Твой новый токен и номер карты)
MONO_TOKEN = "Uppp1adOkmtW3blg-fQQCIqWjnlDH9A-Zu-TgXdXbCFo"
CARD_NUMBER = "4441111002183725"

# Настройки Gramix
GRAMIX_API_KEY = "o1rNmY6Filef---nDBD9FW45hleb-LCLbIOhjmw2irE"
GRAMIX_URL = "https://gramix.io/api/v1/orders"
# ========================================================

router = Router()

# Функция проверки оплаты через карту Monobank
async def check_mono_payment(amount_uah: float) -> bool:
    headers = {"X-Token": MONO_TOKEN}
    
    async with aiohttp.ClientSession() as session:
        # 1. Находим ID гривневого счета (980 = UAH)
        async with session.get("https://api.monobank.ua/personal/client-info", headers=headers) as resp:
            if resp.status != 200:
                return False
            data = await resp.json()
            accounts = data.get("accounts", [])
            
            target_account_id = None
            for acc in accounts:
                if acc.get("currencyCode") == 980:  # Гривна
                    target_account_id = acc.get("id")
                    break
            
            if not target_account_id and accounts:
                target_account_id = accounts[0]["id"]
                
            if not target_account_id:
                return False
        
        # 2. Получаем выписку за последние 24 часа
        to_time = int(time.time())
        from_time = to_time - 86400
        statement_url = f"https://api.monobank.ua/personal/statement/{target_account_id}/{from_time}/{to_time}"
        
        async with session.get(statement_url, headers=headers) as resp:
            if resp.status == 200:
                statement = await resp.json()
                target_amount_cents = int(amount_uah * 100)
                
                for item in statement:
                    if item.get("amount") == target_amount_cents:
                        return True
            return False

# Функция отправки заказа в Gramix
async def fulfill_gramix_order(username: str, amount: int):
    headers = {
        "Authorization": f"Bearer {GRAMIX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "service": "stars",
        "username": username.replace("@", ""),
        "amount": amount
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(GRAMIX_URL, json=payload, headers=headers) as resp:
            if resp.status in (200, 201):
                return True, await resp.json()
            else:
                return False, await resp.text()

# 🚀 Стартовая команда и запрос контакта (как в Wallet)
@router.message(F.text.in_({"/start", "Меню", "Главное меню"}))
async def start_cmd(message: Message):
    kb_contact = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Подтвердить аккаунт (Поделиться контактом)", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"🔥 <b>Добро пожаловать в наш цифровой магазин!</b> 🔥\n\n"
        f"Для безопасности и автоматической выдачи товаров (Telegram Stars / Premium) нам необходимо подтвердить ваш аккаунт Telegram.\n\n"
        f"👇 <b>Нажмите кнопку ниже, чтобы поделиться контактом:</b>",
        reply_markup=kb_contact,
        parse_mode="HTML"
    )

# 📱 Обработка полученного контакта от пользователя
@router.message(F.contact)
async def contact_handler(message: Message):
    user = message.from_user
    username = user.username if user.username else f"id{user.id}"
    
    kb_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звёзды (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Подписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Помощь / Связь с админом", callback_data="help_admin")]
    ])
    
    await message.answer("✅ <b>Аккаунт успешно подтвержден!</b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    
    await message.answer(
        f"🎉 <b>Добро пожаловать в магазин, @{username}!</b> 🔥\n\n"
        "У нас ты можешь моментально и без переплат приобрести ⭐ <b>Telegram Stars</b>, 🖼️ <b>NFT</b> и 💎 <b>Telegram Premium</b>!\n\n"
        "👇 Выбери интересующий раздел ниже:",
        reply_markup=kb_menu,
        parse_mode="HTML"
    )

# 🌟 Раздел Звёзд с прайс-листом
@router.callback_query(F.data == "category_stars")
async def category_stars_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 50 Stars — 42 UAH", callback_data="buy_stars_50_42")],
        [InlineKeyboardButton(text="⭐ 100 Stars — 85 UAH", callback_data="buy_stars_100_85")],
        [InlineKeyboardButton(text="🔥 150 Stars — 120 UAH", callback_data="buy_stars_150_120")],
        [InlineKeyboardButton(text="🚀 200 Stars — 160 UAH", callback_data="buy_stars_200_160")],
        [InlineKeyboardButton(text="👑 Свыше 200 Stars (Написать админу)", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "⭐ <b>Раздел: Telegram Stars</b> ⭐\n\n"
        "⚡ <i>Минимальная сумма пополнения — <b>50 звёзд</b>.</i>\n\n"
        "Какое количество звёзд вы хотите купить?\n"
        "Выберите нужный пакет ниже 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🖼️ Раздел NFT
@router.callback_query(F.data == "category_nft")
async def category_nft_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Связаться с админом", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🖼️ <b>Раздел: Telegram NFT</b> 🖼️\n\n"
        "Покупка и подбор уникальных NFT и Юзернеймов на базе Telegram!\n\n"
        "💬 По всем вопросам о наличии и покупке NFT пиши напрямую администратору: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💎 Раздел Premium
@router.callback_query(F.data == "category_premium")
async def category_premium_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Оформить через админа", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "💎 <b>Раздел: Telegram Premium</b> 💎\n\n"
        "Быстрое и безопасное подсоединение подписки Telegram Premium на 3, 6 или 12 месяцев без входа в аккаунт!\n\n"
        "👇 Напиши нашему админу для оформления: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🆘 Помощь и связь с админом
@router.callback_query(F.data == "help_admin")
async def help_admin_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать админу (@Bodban7)", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🆘 <b>Поддержка и контакты</b> 🆘\n\n"
        "Возник вопрос по заказу, задержке платежа или хочешь уточнить детали?\n\n"
        "👑 <b>Наш Главный Администратор:</b> @Bodban7\n"
        "⏱️ Время ответа: от 2 до 15 минут!",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💰 Экран выбора банка для оплаты (с иконками)
@router.callback_query(F.data.startswith("buy_stars_"))
async def process_buy_stars(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = int(uah_price)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐈 Monobank", callback_data=f"pay_bank_mono_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟩 Приват24", callback_data=f"pay_bank_privat_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟥 А-Банк", callback_data=f"pay_bank_a_bank_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔷 ПУМБ", callback_data=f"pay_bank_pumb_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟣 Сенс Банк (Sense)", callback_data=f"pay_bank_sense_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟡 Ощадбанк", callback_data=f"pay_bank_oshad_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔹 Альянс Банк", callback_data=f"pay_bank_alliance_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="💳 Другой банк Украины", callback_data=f"pay_bank_other_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="category_stars")]
    ])
    
    await callback.message.edit_text(
        f"✨ <b>Оформление заказа: {stars_count} Telegram Stars</b> ⭐\n\n"
        f"💰 <b>Сумма к оплате:</b> <code>{uah_price} UAH</code>\n\n"
        f"👇 Выберите банк, с которого вам удобнее сделать перевод:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 📋 Показ реквизитов после выбора конкретного банка
@router.callback_query(F.data.startswith("pay_bank_"))
async def process_bank_selected(callback: CallbackQuery):
    parts = callback.data.split("_")
    bank_name = "_".join(parts[2:-2])
    stars_count = parts[-2]
    uah_price = parts[-1]
    
    bank_titles = {
        "mono": "Monobank 🐈",
        "privat": "Приват24 🟩",
        "a_bank": "А-Банк 🟥",
        "pumb": "ПУМБ 🔷",
        "sense": "Сенс Банк 🟣",
        "oshad": "Ощадбанк 🟡",
        "alliance": "Альянс Банк 🔹",
        "other": "Другой банк Украины 💳"
    }
    selected_bank = bank_titles.get(bank_name, "Украинский банк")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_pay_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 К выбору банка", callback_data=f"buy_stars_{stars_count}_{uah_price}")]
    ])
    
    await callback.message.edit_text(
        f"✨ <b>Оплата через {selected_bank}</b>\n\n"
        f"📦 <b>Товар:</b> {stars_count} Telegram Stars ⭐\n"
        f"💳 <b>Карта получателя:</b> <code>{CARD_NUMBER}</code>\n"
        f"💰 <b>Сумма к оплате:</b> <code>{uah_price} UAH</code>\n\n"
        f"<b>Инструкция:</b>\n"
        f"1️⃣ Откройте приложение выбранного банка и переведите ровно <b>{uah_price} грн</b> на карту <code>{CARD_NUMBER}</code>.\n"
        f"2️⃣ После успешного перевода нажмите кнопку <b>«✅ Я оплатил»</b> ниже.\n\n"
        f"🚀 Звёзды зачислятся автоматически после проверки!",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ✅ Проверка оплаты
@router.callback_query(F.data.startswith("confirm_pay_"))
async def confirm_payment_handler(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = float(uah_price)
    
    user = callback.from_user
    username = user.username if user.username else f"id{user.id}"

    await callback.message.answer(f"🔍 <b>Ищем твой перевод {int(uah_price)} грн на Monobank...</b>", parse_mode="HTML")
    
    payment_received = await check_mono_payment(amount_uah=uah_price)
    
    if payment_received:
        await callback.message.answer("🎉 <b>Оплата найдена!</b> Отправляем запрос в систему...")
        
        success, res = await fulfill_gramix_order(username=username, amount=stars_count)
        if success:
            await callback.message.answer(
                f"🔥 <b>Ура! Заказ выполнен!</b>\n\n"
                f"⭐ <b>{stars_count} звёзд</b> успешно зачислены на твой аккаунт <b>@{username}</b>!\n"
                f"Спасибо за покупку! Возвращайся ещё! 😉",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                "⚠️ <b>Оплата получена</b>, но произошла небольшая задержка на стороне поставщика.\n"
                "Не волнуйся, уже уведомили администратора! Напиши <b>@Bodban7</b> для быстрой выдачи вручную.",
                parse_mode="HTML"
            )
    else:
        await callback.message.answer(
            f"❌ <b>Оплата {int(uah_price)} грн пока не поступила.</b>\n"
            f"Подожди 10–20 секунд после перевода и нажми кнопку <b>«✅ Я оплатил»</b> ещё раз!",
            parse_mode="HTML"
        )

# 🔙 Назад в меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звёзды (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Подписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Помощь / Связь с админом", callback_data="help_admin")]
    ])
    
    await callback.message.edit_text(
        "🔥 <b>Главное меню</b> 🔥\n\n"
        "👇 Выбери нужную категорию:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ==================== ФОНОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
async def handle_ping(request):
    return web.Response(text="Bot is active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

# ==================== ЗАПУСК БОТА ====================
async def main():
    asyncio.create_task(start_web_server())
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    # Установка постоянной кнопки Меню (Start) слева внизу
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню магазина")
    ])
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
