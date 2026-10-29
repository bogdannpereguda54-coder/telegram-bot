import os
import asyncio
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ==================== МОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8964975943:AAFWqdmtpIAalpnGr7fwEOYk72oTzo20U-s"

# 👑 Твой реальный Telegram ID администратора
ADMIN_ID = 5164361228

# Настройки карты для перевода
CARD_NUMBER = "4441111002183725"

# Настройки Gramix (новый ключ успешно добавлен)
GRAMIX_API_KEY = "U5cxNghXuvKzzQeKIGQNlq7qgWyOcmCCuJ2EVHWnVAg"
GRAMIX_URL = "https://api.gramix.io/api/v1/purchase/stars"

# 🌐 Твой актуальный URL на Render
RENDER_URL = "https://telegram-bot-j0pw.onrender.com"
# ========================================================

# 🛑 Инициализируем роутер
router = Router()
waiting_for_receipt = {}

# Функция автоматической отправки заказа в Gramix по документации API v1
async def fulfill_gramix_order(username: str, amount: int):
    # Генерируем уникальный ключ идемпотентности длиной от 8 до 64 символов
    idempotency_key = f"order_{uuid.uuid4().hex[:16]}"
    
    headers = {
        "x-api-key": GRAMIX_API_KEY,
        "idempotency-key": idempotency_key,
        "Content-Type": "application/json"
    }
    payload = {
        "recipientName": username.replace("@", ""),
        "paymentCurrency": "usdt",
        "stars": amount
    }
    
    print(f"📦 Отправка запроса в Gramix для {username} на {amount} звезд...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GRAMIX_URL, json=payload, headers=headers) as resp:
                response_text = await resp.text()
                print(f"📥 Ответ Gramix [Статус {resp.status}]: {response_text}")
                
                if resp.status in (200, 201):
                    try:
                        return True, await resp.json()
                    except:
                        return True, {"message": response_text}
                else:
                    return False, f"Статус {resp.status}: {response_text}"
        except Exception as e:
            print(f"⚠️ Ошибка соединения с Gramix: {e}")
            return False, str(e)

# 🚀 Стартовая команда
@router.message(F.text.in_({"/start", "Меню", "Главное меню"}))
async def start_cmd(message: Message, bot: Bot):
    user = message.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"

    kb_contact = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Подтвердить аккаунт (Поделиться контактом)", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"🔥 <b>Чего ждешь? Начинай получать звезды прямо сейчас!</b> 🚀\n\n"
        f"Для безопасности и выдачи товаров нам необходимо подтвердить ваш аккаунт Telegram.\n\n"
        f"👇 <b>Нажмите кнопку ниже, чтобы поделиться контактом:</b>",
        reply_markup=kb_contact,
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👀 <b>Клиент зашел в бота:</b> {username} (ID: <code>{user.id}</code>) увидел стартовое окно.",
            parse_mode="HTML"
        )
    except:
        pass

# 📱 Обработка контакта
@router.message(F.contact)
async def contact_handler(message: Message, bot: Bot):
    user = message.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    
    kb_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звезды (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Подписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Помощь / Связь с админом", callback_data="help_admin")]
    ])
    
    await message.answer("✅ <b>Аккаунт успешно подтвержден!</b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    
    await message.answer(
        f"🎉 <b>Добро пожаловать в магазин, {username}!</b> 🔥\n\n"
        "У нас ты можешь приобрести ⭐ <b>Telegram Stars</b>, 🖼️ <b>NFT</b> и 💎 <b>Telegram Premium</b>!\n\n"
        "👇 Выбери нужный раздел ниже:",
        reply_markup=kb_menu,
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 <b>Верификация пройдена!</b> Клиент {username} (ID: <code>{user.id}</code>) подтвердил контакт.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка оповещения админу: {e}")

# 🌟 Раздел Звезд
@router.callback_query(F.data == "category_stars")
async def category_stars_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Смотрит товар:</b> {username} открыл раздел <b>Telegram Stars ⭐</b>", parse_mode="HTML")
    except:
        pass

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
        "⚡ <i>Минимальная сумма пополнения — <b>50 звезд</b>.</i>\n\n"
        "Выберите нужный пакет ниже 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🖼️ Раздел NFT
@router.callback_query(F.data == "category_nft")
async def category_nft_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Смотрит товар:</b> {username} открыл раздел <b>NFT 🖼️</b>", parse_mode="HTML")
    except:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Связаться с админом", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🖼️ <b>Раздел: Telegram NFT</b> 🖼️\n\n"
        "Покупка и подбор уникальных NFT и юзернеймов на базе Telegram!\n\n"
        "💬 По всем вопросам пиши администратору: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💎 Раздел Premium
@router.callback_query(F.data == "category_premium")
async def category_premium_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Смотрит товар:</b> {username} открыл раздел <b>Telegram Premium 💎</b>", parse_mode="HTML")
    except:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Оформить через админа", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "💎 <b>Раздел: Telegram Premium</b> 💎\n\n"
        "Быстрое подключение подписки Telegram Premium без входа в аккаунт!\n\n"
        "👇 Напиши нашему админу для оформления: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🆘 Помощь
@router.callback_query(F.data == "help_admin")
async def help_admin_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать админу (@Bodban7)", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🆘 <b>Поддержка и контакты</b> 🆘\n\n"
        "👑 <b>Главный Администратор:</b> @Bodban7\n"
        "⏱️ Время ответа: от 2 до 15 минут!",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💰 Выбор банка
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
        f"👇 Выберите банк для перевода:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 📋 Показ реквизитов
@router.callback_query(F.data.startswith("pay_bank_"))
async def process_bank_selected(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    bank_name = "_".join(parts[2:-2])
    stars_count = parts[-2]
    uah_price = parts[-1]
    
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📌 <b>Выбрал реквизиты:</b> {username} запросил карту для оплаты <b>{stars_count} Stars</b> ({uah_price} UAH)",
            parse_mode="HTML"
        )
    except:
        pass

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
        f"1️⃣ Переведите ровно <b>{uah_price} грн</b> на карту <code>{CARD_NUMBER}</code>.\n"
        f"2️⃣ После перевода нажмите кнопку <b>«✅ Я оплатил»</b> ниже.",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ✅ Нажатие клиентом «Я оплатил»
@router.callback_query(F.data.startswith("confirm_pay_"))
async def confirm_payment_handler(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = int(uah_price)
    
    user_id = callback.from_user.id

    waiting_for_receipt[user_id] = {
        "stars_count": stars_count,
        "uah_price": uah_price
    }

    await callback.message.edit_text(
        f"📸 <b>Почти готово!</b>\n\n"
        f"📦 Товар: {stars_count} Stars ({uah_price} UAH)\n\n"
        f"👇 Пожалуйста, **скиньте чек (скриншот или фото перевода)** прямо сюда в чат с ботом. Администратор @Bodban7 сразу проверит его и выдаст звезды!",
        parse_mode="HTML"
    )

# 📥 Получение чека
@router.message(F.photo | F.document)
async def receipt_received_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    if user_id not in waiting_for_receipt:
        return

    order_info = waiting_for_receipt.pop(user_id)
    stars_count = order_info["stars_count"]
    uah_price = order_info["uah_price"]
    
    user = message.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"

    await message.answer(
        "⏳ <b>Чек успешно принят и отправлен администратору!</b>\nОжидайте проверки.",
        parse_mode="HTML"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟩 Подтверждено", callback_data=f"adm_yes_{user_id}_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟥 Оплата не обнаружена", callback_data=f"adm_no_{user_id}_{stars_count}")]
    ])

    caption_text = (
        f"🔔 <b>НОВЫЙ ЧЕК НА ПРОВЕРКУ!</b>\n\n"
        f"👤 <b>Клиент:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"📦 <b>Товар:</b> {stars_count} Telegram Stars\n"
        f"💰 <b>Сумма:</b> {uah_price} UAH"
    )

    try:
        if message.photo:
            photo_id = message.photo[-1].file_id
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption_text, reply_markup=admin_kb, parse_mode="HTML")
        elif message.document:
            doc_id = message.document.file_id
            await bot.send_document(chat_id=ADMIN_ID, document=doc_id, caption=caption_text, reply_markup=admin_kb, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка пересылки чека админу: {e}")

# 🟩 Админ нажал «Подтверждено»
@router.callback_query(F.data.startswith("adm_yes_"))
async def admin_approve_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return

    print(f"🔍 Кнопка 'Подтверждено' нажата! callback_data: {callback.data}")

    try:
        parts = callback.data.split("_")
        target_user_id = int(parts[2])
        stars_count = int(parts[3])
        uah_price = int(parts[4])
    except Exception as e:
        print(f"❌ Ошибка разбора callback_data: {e}")
        return

    print(f"✅ Успешно распарсено: UserID={target_user_id}, Stars={stars_count}, UAH={uah_price}")

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟩 <b>Статус: Запрос отправлен в Gramix...</b>", parse_mode="HTML", reply_markup=None)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n🟩 <b>Статус: Запрос отправлен в Gramix...</b>", parse_mode="HTML")

    try:
        chat_member = await bot.get_chat(target_user_id)
        target_username = chat_member.username if chat_member.username else f"id{target_user_id}"
    except:
        target_username = f"id{target_user_id}"

    success, res = await fulfill_gramix_order(username=target_username, amount=stars_count)

    if success:
        if callback.message.caption:
            await callback.message.edit_caption(caption=callback.message.caption.replace("🟩 <b>Статус: Запрос отправлен в Gramix...</b>", "✅ <b>Статус: Успешно выдано через Gramix!</b>"), parse_mode="HTML")
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"🎉 <b>Оплата подтверждена администратором!</b>\n\n"
                    f"⭐ <b>{stars_count} звезд</b> успешно зачислены на ваш аккаунт!\n"
                    f"Спасибо за покупку! 😉"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Не удалось написать клиенту: {e}")
    else:
        error_msg = str(res)[:300]
        if callback.message.caption:
            await callback.message.edit_caption(caption=callback.message.caption.replace("🟩 <b>Статус: Запрос отправлен в Gramix...</b>", f"❌ <b>Ошибка Gramix:</b> <code>{error_msg}</code>"), parse_mode="HTML")

# 🟥 Админ нажал «Оплата не обнаружена»
@router.callback_query(F.data.startswith("adm_no_"))
async def admin_reject_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return

    try:
        parts = callback.data.split("_")
        target_user_id = int(parts[-2])
    except:
        target_user_id = 0

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟥 <b>Статус: Оплата не обнаружена (Отклонено).</b>", parse_mode="HTML", reply_markup=None)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n🟥 <b>Статус: Оплата не обнаружена (Отклонено).</b>", parse_mode="HTML")

    if target_user_id:
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text="❌ <b>Оплата по чеку не обнаружена или отклонена администратором.</b>\nЕсли вы считаете, что это ошибка, напишите администратору: @Bodban7",
                parse_mode="HTML"
            )
        except:
            pass

# 🔙 Назад в меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звезды (Telegram Stars)", callback_data="category_stars")],
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

# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================
async def handle_ping(request):
    return web.Response(text="Bot is active!")

async def keep_alive_ping():
    await asyncio.sleep(15)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if "onrender.com" in RENDER_URL:
                    async with session.get(RENDER_URL) as resp:
                        print(f"🔄 Самопинг сервера выполнен. Статус: {resp.status}")
            except Exception as e:
                print(f"⚠️ Ошибка самопинга: {e}")
            await asyncio.sleep(600)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню магазина")
    ])
    
    # 💥 СБРОСИТЬ ВСЕ ЗАВИСШИЕ СЕССИИ И ВЕБХУКИ ПЕРЕД ЗАПУСКОМ
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(2)

    asyncio.create_task(keep_alive_ping())
    
    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Веб-сервер запущен на порту {port}")

    print("🤖 Бот запущен и полностью готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
