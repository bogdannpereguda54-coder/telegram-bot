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
            await callback.message.edit_caption(caption=callback.message.caption.replace("🟩 <b>Статус: Запрос отправлен в Gramix...</b>", "✅ <b>Статус: Успешно выдано!</b>"), parse_mode="HTML")
        
        try:
            await bot.send_message(
                chat_id=target_user_id,
                text=(
                    f"🎉 <b>Оплата подтверждена администратором!</b>\n\n"
                    f"⭐ <b>{stars_count} звёзд</b> успешно зачислены на ваш аккаунт!\n"
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
