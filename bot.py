import os
import time
import asyncio
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand, ReplyKeyboardRemove

# ==================== МОИ НАСТРОЙКИ ====================
BOT_TOKEN = "8964975943:AAGn_sPgDWCUni140MGJNYxVAyqOwHNWM-8"
MONO_TOKEN = "Uppp1adOkmtW3blg-fQQCIqWjnlDH9A-Zu-TgXdXbCFo"
CARD_NUMBER = "4441111002183725"

GRAMIX_API_KEY = "o1rNmY6Filef---nDBD9FW45hleb-LCLbIOhjmw2irE"
GRAMIX_URL = "https://gramix.io/api/v1/orders"
# ========================================================

router = Router()

# Функция проверки оплаты с отладкой
async def check_mono_payment_debug(amount_uah: float):
    headers = {"X-Token": MONO_TOKEN}
    debug_log = []
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.monobank.ua/personal/client-info", headers=headers) as resp:
            if resp.status != 200:
                return False, f"Ошибка client-info: {resp.status}"
            data = await resp.json()
            accounts = data.get("accounts", [])
            
            uah_account_ids = [acc.get("id") for acc in accounts if acc.get("currencyCode") == 980]
            if not uah_account_ids and accounts:
                uah_account_ids = [acc.get("id") for acc in accounts]
                
            if not uah_account_ids:
                return False, "Не найдены счета в Monobank"
        
        to_time = int(time.time())
        from_time = to_time - 1200  # За последние 20 минут
        target_amount_cents = int(amount_uah * 100)
        
        debug_log.append(f"Ищем сумму: {target_amount_cents} коп ({amount_uah} грн)")
        
        for account_id in uah_account_ids:
            statement_url = f"https://api.monobank.ua/personal/statement/{account_id}/{from_time}/{to_time}"
            async with session.get(statement_url, headers=headers) as resp:
                if resp.status == 200:
                    statement = await resp.json()
                    debug_log.append(f"Счет {account_id[:6]}...: найдено транзакций: {len(statement)}")
                    for item in statement:
                        amt = item.get("amount")
                        comment = item.get("comment", "нет коммента")
                        debug_log.append(f"-> Транзакция: {amt} коп ({comment})")
                        if amt == target_amount_cents:
                            return True, "Успех! Платеж найден."
                else:
                    debug_log.append(f"Ошибка выписки по счету {resp.status}")
                    
        return False, "\n".join(debug_log)

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

# 🚀 Стартовая команда и запрос контакта
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
        f"Для безопасности и автоматической выдачи товаров нам необходимо подтвердить ваш аккаунт Telegram.\n\n"
        f"👇 <b>Нажмите кнопку ниже, чтобы поделиться контактом:</b>",
        reply_markup=kb_contact,
        parse_mode="HTML"
    )

# 📱 Обработка контакта
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
        "👇 Выбери интересующий раздел ниже:",
        reply_markup=kb_menu,
        parse_mode="HTML"
    )

# 🌟 Раздел Звёзд
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
        "⭐ <b>Раздел: Telegram Stars</b> ⭐\n\nВыберите нужный пакет ниже 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "category_nft")
async def category_nft_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Связаться с админом", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("🖼️ <b>Раздел: Telegram NFT</b> 🖼️\n\nПиши администратору: <b>@Bodban7</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "category_premium")
async def category_premium_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Оформить через админа", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("💎 <b>Раздел: Telegram Premium</b> 💎\n\nПиши администратору: <b>@Bodban7</b>", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "help_admin")
async def help_admin_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать админу", url="https://t.me/Bodban7")],
        [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
    ])
    await callback.message.edit_text("🆘 <b>Поддержка</b>\n\nАдминистратор: @Bodban7", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("buy_stars_"))
async def process_buy_stars(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = int(uah_price)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐈 Monobank", callback_data=f"pay_bank_mono_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="category_stars")]
    ])
    await callback.message.edit_text(
        f"✨ <b>Оформление заказа: {stars_count} Telegram Stars</b> ⭐\n\n"
        f"💰 <b>Сумма к оплате:</b> <code>{uah_price} UAH</code>\n\n👇 Выберите банк:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("pay_bank_"))
async def process_bank_selected(callback: CallbackQuery):
    parts = callback.data.split("_")
    stars_count = parts[-2]
    uah_price = parts[-1]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"confirm_pay_{stars_count}_{uah_price}")],
        [InlineKeyboardButton(text="🔙 К выбору", callback_data=f"buy_stars_{stars_count}_{uah_price}")]
    ])
    await callback.message.edit_text(
        f"✨ <b>Оплата через Monobank 🐈</b>\n\n"
        f"💳 <b>Карта:</b> <code>{CARD_NUMBER}</code>\n"
        f"💰 <b>Сумма:</b> <code>{uah_price} UAH</code>\n\n"
        f"Переведите сумму и нажмите <b>«✅ Я оплатил»</b>.",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ✅ Проверка с отладкой
@router.callback_query(F.data.startswith("confirm_pay_"))
async def confirm_payment_handler(callback: CallbackQuery):
    _, _, stars_count, uah_price = callback.data.split("_")
    stars_count = int(stars_count)
    uah_price = float(uah_price)
    
    user = callback.from_user
    username = user.username if user.username else f"id{user.id}"

    msg = await callback.message.answer(f"🔍 <b>Проверяем выписку Monobank...</b>", parse_mode="HTML")
    
    is_found, debug_info = await check_mono_payment_debug(amount_uah=uah_price)
    
    if is_found:
        await msg.edit_text("🎉 <b>Оплата найдена!</b> Выдаем звёзды...")
        success, res = await fulfill_gramix_order(username=username, amount=stars_count)
        if success:
            await callback.message.answer(f"🔥 <b>Заказ выполнен!</b> ⭐ {stars_count} звёзд зачислено на @{username}!")
        else:
            await callback.message.answer("⚠️ Оплата получена, но ошибка Gramix. Напиши админу @Bodban7.")
    else:
        await msg.edit_text(
            f"❌ <b>Платеж не найден.</b>\n\n"
            f"📋 <b>Диагностика API:</b>\n<pre>{debug_info}</pre>",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "back_to_main")
async def back_to_main_handler(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Звёзды (Telegram Stars)", callback_data="category_stars")],
        [InlineKeyboardButton(text="🖼️ Telegram NFT", callback_data="category_nft")],
        [InlineKeyboardButton(text="💎 Подписки Telegram Premium", callback_data="category_premium")],
        [InlineKeyboardButton(text="🆘 Помощь / Связь с админом", callback_data="help_admin")]
    ])
    await callback.message.edit_text("🔥 <b>Главное меню</b>", reply_markup=kb, parse_mode="HTML")

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

async def main():
    asyncio.create_task(start_web_server())
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await bot.set_my_commands([BotCommand(command="start", description="Главное меню")])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
