import os
import asyncio
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8964975943:AAFj1AqyppqWFHxD5oQ1v2IOr9mVVPVfPt4"
GRAMIX_API_KEY = os.environ.get("GRAMIX_API_KEY")

ADMIN_ID = 5164361228
CARD_NUMBER = "4441111002183725"

GRAMIX_URL = "https://api.gramix.io/api/v1/purchase/stars"

WEBHOOK_URL = "https://telegram-bot-j0pw.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SERVER_URL = f"{WEBHOOK_URL}{WEBHOOK_PATH}"
# ===================================================

router = Router()
waiting_for_receipt = {}


# ==================== GRAMIX ====================
async def fulfill_gramix_order(username: str, amount: int):
    """Заказ звезд в Gramix. Получатель указывается по username (без @, в нижнем регистре)."""
    if not GRAMIX_API_KEY:
        print("❌ Переменная окружения GRAMIX_API_KEY не задана на сервере!")
        return False, "API ключ Gramix не настроен на сервере"

    recipient = str(username).strip().lstrip("@").lower()
    idempotency_key = f"order_{uuid.uuid4().hex}"
    print(f"📦 Заказ в Gramix: recipientName={recipient}, stars={amount}")

    headers = {
        "x-api-key": GRAMIX_API_KEY,
        "idempotency-key": idempotency_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "recipientName": recipient,
        "paymentCurrency": "usdt",
        "stars": amount,
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(GRAMIX_URL, json=payload, headers=headers) as resp:
                response_text = await resp.text()
                print(f"📥 Ответ Gramix [Статус {resp.status}]: {response_text}")

                if resp.status in (200, 201):
                    return True, response_text
                return False, f"Статус {resp.status}: {response_text}"
        except Exception as e:
            print(f"⚠️ Ошибка соединения с Gramix: {e}")
            return False, str(e)


# ==================== КЛИЕНТ ====================
def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звезды (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Подписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Помощь / Связь с админом", callback_data="help_admin")]
    ])


def get_username(user) -> str:
    return f"@{user.username}" if user.username else f"id{user.id}"


async def notify_admin(bot: Bot, text: str):
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка оповещения админу: {e}")


# 🚀 Старт
@router.message(F.text.in_({"/start", "Меню", "Главное меню"}))
async def start_cmd(message: Message, bot: Bot):
    user = message.from_user

    kb_contact = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Подтвердить аккаунт (Поделиться контактом)", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "🔥 <b>Чего ждешь? Начинай получать звезды прямо сейчас!</b> 🚀\n\n"
        "Для безопасности и выдачи товаров нам необходимо подтвердить ваш аккаунт Telegram.\n\n"
        "⚠️ <b>Для получения звезд у вас должен быть установлен username</b> "
        "(Настройки → Имя пользователя).\n\n"
        "👇 <b>Нажмите кнопку ниже, чтобы поделиться контактом:</b>",
        reply_markup=kb_contact,
        parse_mode="HTML"
    )

    await notify_admin(
        bot,
        f"👀 <b>Клиент зашел в бота:</b> {get_username(user)} (ID: <code>{user.id}</code>) увидел стартовое окно."
    )


# 📱 Контакт
@router.message(F.contact)
async def contact_handler(message: Message, bot: Bot):
    user = message.from_user
    username = get_username(user)

    await message.answer("✅ <b>Аккаунт успешно подтвержден!</b>", reply_markup=ReplyKeyboardRemove(), parse_mode="HTML")

    await message.answer(
        f"🎉 <b>Добро пожаловать в магазин, {username}!</b> 🔥\n\n"
        "У нас ты можешь приобрести ⭐ <b>Telegram Stars</b>, 🖼️ <b>NFT</b> и 💎 <b>Telegram Premium</b>!\n\n"
        "👇 Выбери нужный раздел ниже:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

    await notify_admin(
        bot,
        f"👤 <b>Верификация пройдена!</b> Клиент {username} (ID: <code>{user.id}</code>) подтвердил контакт."
    )


# 🌟 Раздел Звезд
@router.callback_query(F.data == "category_stars")
async def category_stars_handler(callback: CallbackQuery, bot: Bot):
    await notify_admin(
        bot,
        f"👀 <b>Смотрит товар:</b> {get_username(callback.from_user)} открыл раздел <b>Telegram Stars ⭐</b>"
    )

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
    await notify_admin(
        bot,
        f"👀 <b>Смотрит товар:</b> {get_username(callback.from_user)} открыл раздел <b>NFT 🖼️</b>"
    )

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
    await notify_admin(
        bot,
        f"👀 <b>Смотрит товар:</b> {get_username(callback.from_user)} открыл раздел <b>Telegram Premium 💎</b>"
    )

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


# 📋 Реквизиты
@router.callback_query(F.data.startswith("pay_bank_"))
async def process_bank_selected(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    bank_name = "_".join(parts[2:-2])
    stars_count = parts[-2]
    uah_price = parts[-1]

    await notify_admin(
        bot,
        f"📌 <b>Выбрал реквизиты:</b> {get_username(callback.from_user)} запросил карту для оплаты "
        f"<b>{stars_count} Stars</b> ({uah_price} UAH)"
    )

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


# ✅ «Я оплатил»
@router.callback_query(F.data.startswith("confirm_pay_"))
async def confirm_payment_handler(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = int(uah_price)

    if not callback.from_user.username:
        await callback.answer(
            "⚠️ Установите username в настройках Telegram (Настройки → Имя пользователя) и нажмите кнопку снова.",
            show_alert=True
        )
        return

    waiting_for_receipt[callback.from_user.id] = {
        "stars_count": stars_count,
        "uah_price": uah_price
    }

    await callback.message.edit_text(
        f"📸 <b>Почти готово!</b>\n\n"
        f"📦 Товар: {stars_count} Stars ({uah_price} UAH)\n\n"
        f"👇 Пожалуйста, <b>скиньте чек (скриншот или фото перевода)</b> прямо сюда в чат с ботом. "
        f"Администратор @Bodban7 сразу проверит его и выдаст звезды!",
        parse_mode="HTML"
    )


# 📥 Получение чека
@router.message(F.photo | F.document)
async def receipt_received_handler(message: Message, bot: Bot):
    user = message.from_user
    user_id = user.id

    if user_id not in waiting_for_receipt:
        return

    order_info = waiting_for_receipt.pop(user_id)
    stars_count = order_info["stars_count"]
    uah_price = order_info["uah_price"]
    username = get_username(user)

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
            await bot.send_photo(
                chat_id=ADMIN_ID, photo=message.photo[-1].file_id,
                caption=caption_text, reply_markup=admin_kb, parse_mode="HTML"
            )
        else:
            await bot.send_document(
                chat_id=ADMIN_ID, document=message.document.file_id,
                caption=caption_text, reply_markup=admin_kb, parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка пересылки чека админу: {e}")


# ==================== АДМИН ====================
async def set_admin_status(callback: CallbackQuery, status_text: str, remove_buttons: bool = True):
    base = callback.message.html_text if hasattr(callback.message, "html_text") else ""
    base = base or ""
    if "\n\n🟩 <b>Статус" in base:
        base = base.split("\n\n🟩 <b>Статус")[0]
    if "\n\n✅ <b>Статус" in base:
        base = base.split("\n\n✅ <b>Статус")[0]
    if "\n\n❌ <b>Ошибка" in base:
        base = base.split("\n\n❌ <b>Ошибка")[0]

    new_text = f"{base}\n\n{status_text}"
    kwargs = {"parse_mode": "HTML"}
    if remove_buttons:
        kwargs["reply_markup"] = None

    try:
        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=new_text, **kwargs)
        else:
            await callback.message.edit_text(text=new_text, **kwargs)
    except Exception as e:
        print(f"⚠️ Не удалось обновить сообщение: {e}")


# 🟩 «Подтверждено»
@router.callback_query(F.data.startswith("adm_yes_"))
async def admin_approve_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return

    try:
        parts = callback.data.split("_")
        target_user_id = int(parts[2])
        stars_count = int(parts[3])
    except Exception as e:
        print(f"❌ Ошибка разбора callback_data: {e}")
        await callback.answer(f"Ошибка парсинга: {e}", show_alert=True)
        return

    username = ""
    try:
        chat = await bot.get_chat(target_user_id)
        username = (chat.username or "").lower()
    except Exception as e:
        print(f"⚠️ Не удалось получить username: {e}")

    if not username:
        await callback.answer(
            "❌ У клиента нет username. Попросите установить его в настройках Telegram и пришлите чек заново.",
            show_alert=True
        )
        return

    await callback.answer("⏳ Обработка заказа...")
    await set_admin_status(callback, f"🟩 <b>Статус: Запрос отправлен в Gramix (@{username})...</b>")

    success, res = await fulfill_gramix_order(username=username, amount=stars_count)

    if success:
        await set_admin_status(callback, "✅ <b>Статус: Успешно выдано через Gramix!</b>")
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
        error_msg = str(res)[:300].replace("<", "&lt;").replace(">", "&gt;")
        await set_admin_status(callback, f"❌ <b>Ошибка Gramix:</b> <code>{error_msg}</code>")


# 🟥 «Оплата не обнаружена»
@router.callback_query(F.data.startswith("adm_no_"))
async def admin_reject_order(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав администратора!", show_alert=True)
        return

    try:
        target_user_id = int(callback.data.split("_")[2])
    except Exception:
        target_user_id = 0

    await callback.answer()
    await set_admin_status(callback, "🟥 <b>Статус: Оплата не обнаружена (Отклонено).</b>")

    if target_user_id:
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    "❌ <b>Оплата по чеку не обнаружена или отклонена администратором.</b>\n"
                    "Если вы считаете, что это ошибка, напишите администратору: @Bodban7"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass


# 🔙 Назад в меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔥 <b>Главное меню</b> 🔥\n\n"
        "👇 Выбери нужную категорию:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


# ==================== ЗАПУСК ====================
async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задана переменная окружения BOT_TOKEN (Render → Environment)")

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="🏠 Главное меню магазина")
    ])

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    async def on_startup(app):
        await bot.set_webhook(WEBHOOK_SERVER_URL, drop_pending_updates=True)
        print(f"🌐 Вебхук установлен на: {WEBHOOK_SERVER_URL}")

    app.on_startup.append(on_startup)

    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Запуск бота в режиме Webhook на порту {port}...")

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
