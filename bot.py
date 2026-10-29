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

# Настройки Gramix (используем правильный эндпоинт для покупки звезд и USDT на балансе)
GRAMIX_API_KEY = "o1rNmY6Filef---nDBD9FW45hleb-LCLbIOhjmw2irE"
GRAMIX_URL = "https://api.gramix.io/api/v1/purchase/stars"

# 🌐 Твой актуальный URL на Render
RENDER_URL = "https://telegram-bot-j0pw.onrender.com"
# ========================================================

# 🛑 Инициализируем роутер
router = Router()
waiting_for_receipt = {}

# Функция автоматической отправки заказа в Gramix по документации API v1
async def fulfill_gramix_order(username: str, amount: int):
    # Генеруємо унікальний ключ ідемпотентності довжиною від 8 до 64 символів
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
    
    print(f"📦 Відправка запиту в Gramix для {username} на {amount} зірок...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GRAMIX_URL, json=payload, headers=headers) as resp:
                response_text = await resp.text()
                print(f"📥 Відповідь Gramix [Статус {resp.status}]: {response_text}")
                
                if resp.status in (200, 201):
                    try:
                        return True, await resp.json()
                    except:
                        return True, {"message": response_text}
                else:
                    return False, f"Статус {resp.status}: {response_text}"
        except Exception as e:
            print(f"⚠️ Помилка з'єднання з Gramix: {e}")
            return False, str(e)

# 🚀 Стартова команда
@router.message(F.text.in_({"/start", "Меню", "Главное меню"}))
async def start_cmd(message: Message, bot: Bot):
    user = message.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"

    kb_contact = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Підтвердити акаунт (Поділитися контактом)", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(
        f"🔥 <b>Чого чекаєш? Починай отримувати зірки прямо зараз!</b> 🚀\n\n"
        f"Для безпеки та видачі товарів нам необхідно підтвердити ваш акаунт Telegram.\n\n"
        f"👇 <b>Натисніть кнопку нижче, щоб поділитися контактом:</b>",
        reply_markup=kb_contact,
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👀 <b>Клієнт зайшов у бота:</b> {username} (ID: <code>{user.id}</code>) побачив стартове вікно.",
            parse_mode="HTML"
        )
    except:
        pass

# 📱 Обробка контакту
@router.message(F.contact)
async def contact_handler(message: Message, bot: Bot):
    user = message.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    
    kb_menu = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Зірки (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Підписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Допомога / Зв'язок з адміном", callback_data="help_admin")]
    ])
    
    await message.answer("✅ <b>Акаунт успішно підтверджено!</b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")
    
    await message.answer(
        f"🎉 <b>Ласкаво просимо в магазин, {username}!</b> 🔥\n\n"
        "У нас ти можеш придбати ⭐ <b>Telegram Stars</b>, 🖼️ <b>NFT</b> та 💎 <b>Telegram Premium</b>!\n\n"
        "👇 Обери потрібний розділ нижче:",
        reply_markup=kb_menu,
        parse_mode="HTML"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"👤 <b>Верифікацію пройдено!</b> Клієнт {username} (ID: <code>{user.id}</code>) підтвердив контакт.",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Помилка сповіщення адміну: {e}")

# 🌟 Розділ Зірок
@router.callback_query(F.data == "category_stars")
async def category_stars_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Дивиться товар:</b> {username} відкрив розділ <b>Telegram Stars ⭐</b>", parse_mode="HTML")
    except:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ 50 Stars — 42 UAH", callback_data="buy_stars_50_42")],
        [InlineKeyboardButton(text="⭐ 100 Stars — 85 UAH", callback_data="buy_stars_100_85")],
        [InlineKeyboardButton(text="🔥 150 Stars — 120 UAH", callback_data="buy_stars_150_120")],
        [InlineKeyboardButton(text="🚀 200 Stars — 160 UAH", callback_data="buy_stars_200_160")],
        [InlineKeyboardButton(text="👑 Понад 200 Stars (Написати адміну)", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "⭐ <b>Розділ: Telegram Stars</b> ⭐\n\n"
        "⚡ <i>Мінімальна сума поповнення — <b>50 зірок</b>.</i>\n\n"
        "Оберіть потрібний пакет нижче 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🖼️ Розділ NFT
@router.callback_query(F.data == "category_nft")
async def category_nft_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Дивиться товар:</b> {username} відкрив розділ <b>NFT 🖼️</b>", parse_mode="HTML")
    except:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Зв'язатися з адміном", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🖼️ <b>Розділ: Telegram NFT</b> 🖼️\n\n"
        "Купівля та підбір унікальних NFT та юзернеймів на базі Telegram!\n\n"
        "💬 З усіх питань пиши адміністратору: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💎 Розділ Premium
@router.callback_query(F.data == "category_premium")
async def category_premium_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    username = f"@{user.username}" if user.username else f"id{user.id}"
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"👀 <b>Дивиться товар:</b> {username} відкрив розділ <b>Telegram Premium 💎</b>", parse_mode="HTML")
    except:
        pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Оформити через адміна", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "💎 <b>Розділ: Telegram Premium</b> 💎\n\n"
        "Швидке підключення підписки Telegram Premium без входу в акаунт!\n\n"
        "👇 Напиши нашому адміну для оформлення: <b>@Bodban7</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 🆘 Допомога
@router.callback_query(F.data == "help_admin")
async def help_admin_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написати адміну (@Bodban7)", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад до меню", callback_data="back_to_main")]
    ])
    
    await callback.message.edit_text(
        "🆘 <b>Підтримка та контакти</b> 🆘\n\n"
        "👑 <b>Головний Адміністратор:</b> @Bodban7\n"
        "⏱️ Час відповіді: від 2 до 15 хвилин!",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 💰 Вибір банку
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
        [InlineKeyboardButton(text="💳 Інший банк України", callback_data=f"pay_bank_other_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 Назад до вибору", callback_data="category_stars")]
    ])
    
    await callback.message.edit_text(
        f"✨ <b>Оформлення замовлення: {stars_count} Telegram Stars</b> ⭐\n\n"
        f"💰 <b>Сума до сплати:</b> <code>{uah_price} UAH</code>\n\n"
        f"👇 Оберіть банк для переказу:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# 📋 Показ реквізитів
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
            text=f"📌 <b>Обрав реквізити:</b> {username} запросив картку для оплати <b>{stars_count} Stars</b> ({uah_price} UAH)",
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
        "other": "Інший банк України 💳"
    }
    selected_bank = bank_titles.get(bank_name, "Український банк")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я сплатив", callback_data=f"confirm_pay_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 До вибору банку", callback_data=f"buy_stars_{stars_count}_{uah_price}")]
    ])
    
    await callback.message.edit_text(
        f"✨ <b>Оплата через {selected_bank}</b>\n\n"
        f"📦 <b>Товар:</b> {stars_count} Telegram Stars ⭐\n"
        f"💳 <b>Картка отримувача:</b> <code>{CARD_NUMBER}</code>\n"
        f"💰 <b>Сума до сплати:</b> <code>{uah_price} UAH</code>\n\n"
        f"<b>Інструкція:</b>\n"
        f"1️⃣ Переведіть рівно <b>{uah_price} грн</b> на картку <code>{CARD_NUMBER}</code>.\n"
        f"2️⃣ Після переказу натисніть кнопку <b>«✅ Я сплатив»</b> нижче.",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ✅ Натискання клієнтом «Я сплатив»
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
        f"📸 <b>Майже готово!</b>\n\n"
        f"📦 Товар: {stars_count} Stars ({uah_price} UAH)\n\n"
        f"👇 Будь ласка, **скиньте чек (скріншот або фото переказу)** прямо сюди в чат з ботом. Адміністратор @Bodban7 одразу перевірить його та видасть зірки!",
        parse_mode="HTML"
    )

# 📥 Отримання чека
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
        "⏳ <b>Чек успішно прийнято та відправлено адміністратору!</b>\nОчікуйте перевірки.",
        parse_mode="HTML"
    )

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟩 Підтверджено", callback_data=f"adm_yes_{user_id}_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🟥 Оплату не виявлено", callback_data=f"adm_no_{user_id}_{stars_count}")]
    ])

    caption_text = (
        f"🔔 <b>НОВИЙ ЧЕК НА ПЕРЕВІРКУ!</b>\n\n"
        f"👤 <b>Клієнт:</b> {username} (ID: <code>{user_id}</code>)\n"
        f"📦 <b>Товар:</b> {stars_count} Telegram Stars\n"
        f"💰 <b>Сума:</b> {uah_price} UAH"
    )

    try:
        if message.photo:
            photo_id = message.photo[-1].file_id
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=caption_text, reply_markup=admin_kb, parse_mode="HTML")
        elif message.document:
            doc_id = message.document.file_id
            await bot.send_document(chat_id=ADMIN_ID, document=doc_id, caption=caption_text, reply_markup=admin_kb, parse_mode="HTML")
    except Exception as e:
        print(f"Помилка пересилання чека адміну: {e}")

# 🟩 Адмін натиснув «Підтверджено»
@router.callback_query(F.data.startswith("adm_yes_"))
async def admin_approve_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас немає прав адміністратора!", show_alert=True)
        return

    print(f"🔍 Кнопку 'Підтверджено' натиснуто! callback_data: {callback.data}")

    try:
        parts = callback.data.split("_")
        target_user_id = int(parts[2])
        stars_count = int(parts[3])
        uah_price = int(parts[4])
    except Exception as e:
        print(f"❌ Помилка розбору callback_data: {e}")
        return

    print(f"✅ Успішно розпарсено: UserID={target_user_id}, Stars={stars_count}, UAH={uah_price}")

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟩 <b>Статус: Запит відправлено в Gramix...</b>", parse_mode="HTML", reply_markup=None)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n🟩 <b>Статус: Запит відправлено в Gramix...</b>", parse_mode="HTML")

    try:
        chat_member = await bot.get_chat(target_user_id)
        target_username = chat_member.username if chat_member.username else f"id{target_user_id}"
    except:
        target_username = f"id{target_user_id}"

    success, res = await fulfill_gramix_order(username=target_username, amount=stars_count)

    if success:
        if callback.message.caption:
            await callback.message.edit_caption(caption=callback.message.caption.replace("🟩 <b>Статус: Запит відправлено в Gramix...</b>", "✅ <b>Статус: Успішно видано через Gramix!</b>"), parse_mode="HTML")
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"🎉 <b>Оплату підтверджено адміністратором!</b>\n\n"
                    f"⭐ <b>{stars_count} зірок</b> успішно зараховані на ваш акаунт!\n"
                    f"Дякуємо за покупку! 😉"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Не вдалося написати клієнту: {e}")
    else:
        error_msg = str(res)[:300]
        if callback.message.caption:
            await callback.message.edit_caption(caption=callback.message.caption.replace("🟩 <b>Статус: Запит відправлено в Gramix...</b>", f"❌ <b>Помилка Gramix:</b> <code>{error_msg}</code>"), parse_mode="HTML")

# 🟥 Адмін натиснув «Оплату не виявлено»
@router.callback_query(F.data.startswith("adm_no_"))
async def admin_reject_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас немає прав адміністратора!", show_alert=True)
        return

    try:
        parts = callback.data.split("_")
        target_user_id = int(parts[-2])
    except:
        target_user_id = 0

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n🟥 <b>Статус: Оплату не виявлено (Відхилено).</b>", parse_mode="HTML", reply_markup=None)
    else:
        await callback.message.edit_text(callback.message.text + "\n\n🟥 <b>Статус: Оплату не виявлено (Відхилено).</b>", parse_mode="HTML")

    if target_user_id:
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text="❌ <b>Оплату за чеком не виявлено або відхилено адміністратором.</b>\nЯкщо ви вважаєте, що це помилка, напишіть адміністратору: @Bodban7",
                parse_mode="HTML"
            )
        except:
            pass

# 🔙 Назад до меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Зірки (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Підписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Допомога / Зв'язок з адміном", callback_data="help_admin")]
    ])
    
    await callback.message.edit_text(
        "🔥 <b>Головне меню</b> 🔥\n\n"
        "👇 Обери потрібну категорію:",
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
                        print(f"🔄 Самопінг сервера виконано. Статус: {resp.status}")
            except Exception as e:
                print(f"⚠️ Помилка самопінгу: {e}")
            await asyncio.sleep(600)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Головне меню магазину")
    ])
    
    # 💥 СКИНУТИ ВСІ ЗАВИСЛІ СЕСІЇ ТА ВЕБХУКИ ПЕРЕД ЗАПУСКОМ
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
    print(f"🌐 Веб-сервер запущено на порту {port}")

    print("🤖 Бот запущено і повністю готовий до роботи!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
