from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions
from datetime import datetime, timedelta
from database_json import *
from config import ADMIN_IDS

router = Router()


# Вспомогательные функции
def is_admin_or_has_perm(user_id: int, perm: str) -> bool:
    return user_id in ADMIN_IDS or has_permission(user_id, perm)


def get_user_mention(user: Dict) -> str:
    if user.get("username"):
        return f"@{user['username']}"
    return f"<a href='tg://user?id={user['user_id']}'>{user.get('first_name', 'Пользователь')}</a>"


# ==================== МОДЕРАЦИЯ ====================

@router.message(Command("mute"))
async def cmd_mute(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "mute"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    args = message.text.split()
    minutes = int(args[1]) if len(args) > 1 and args[1].isdigit() else 60
    
    create_user(target.id, target.username or "", target.first_name)
    until = int((datetime.now() + timedelta(minutes=minutes)).timestamp())
    update_user(target.id, is_muted=True, mute_until=until)
    
    try:
        await message.chat.restrict(target.id, ChatPermissions(can_send_messages=False), until_date=until)
    except:
        pass
    
    await message.reply(f"🔇 {get_user_mention({'user_id': target.id, 'username': target.username, 'first_name': target.first_name})} заткнут на {minutes} мин.")


@router.message(Command("unmute"))
async def cmd_unmute(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "mute"):
        return await message.reply("❌ у тя нет прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    update_user(target.id, is_muted=False, mute_until=0)
    
    try:
        await message.chat.restrict(target.id, ChatPermissions(can_send_messages=True, can_send_media=True, can_send_other=True))
    except:
        pass
    
    await message.reply(f"🔊 {target.first_name} дали право болтать.")


@router.message(Command("ban"))
async def cmd_ban(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "ban"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    create_user(target.id, target.username or "", target.first_name)
    update_user(target.id, is_banned=True)
    
    try:
        await message.chat.ban(target.id)
    except:
        pass
    
    await message.reply(f"🚫 {target.first_name} забанен.")


@router.message(Command("unban"))
async def cmd_unban(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "ban"):
        return await message.reply("❌ Недостаточно прав.")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Укажите ID или username: /unban @user")
    
    try:
        if args[1].startswith("@"):
            target_id = None
        else:
            target_id = int(args[1])
        await message.chat.unban(target_id)
        if target_id:
            update_user(target_id, is_banned=False)
        await message.reply(f"✅ Пользователь {args[1]} разбанен.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@router.message(Command("kick"))
async def cmd_kick(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "kick"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    try:
        await message.chat.ban(target.id)
        await message.chat.unban(target.id)
        await message.reply(f"👢 {target.first_name} кикнут.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@router.message(Command("pin"))
async def cmd_pin(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "pin"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение для закрепления.")
    
    try:
        await message.reply_to_message.pin()
        await message.reply("📌 Сообщение закреплено.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@router.message(Command("unpin"))
async def cmd_unpin(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "pin"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение для открепления.")
    
    try:
        await message.reply_to_message.unpin()
        await message.reply("📌 Сообщение откреплено.")
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")


@router.message(Command("delete"))
async def cmd_delete(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "delete"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение для удаления.")
    
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except:
        pass


@router.message(Command("cleanup"))
async def cmd_cleanup(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "cleanup"):
        return await message.reply("❌ Недостаточно прав.")
    
    args = message.text.split()
    limit = int(args[1]) if len(args) > 1 and args[1].isdigit() else 100
    
    try:
        deleted = 0
        async for msg in message.chat.history(limit=limit + 1):
            if msg.from_user and msg.from_user.id == message.bot.id:
                await msg.delete()
                deleted += 1
        await message.reply(f"🧹 Удалено {deleted} сообщений бота.", reply=False)
    except:
        pass


# ==================== РОЛИ И ДОСТУПЫ ====================

@router.message(Command("roles"))
async def cmd_roles(message: types.Message):
    text = "📋 **Доступные роли:**\n\n"
    for role, perms in _data["roles"].items():
        text += f"• **{role}** — `{perms}`\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("role"))
async def cmd_role(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только администраторы могут выдавать роли.")
    
    args = message.text.split()
    if len(args) < 3:
        return await message.reply("❌ Использование: /role @user роль\nДля снятия: /role @user -роль")
    
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    role = args[2]
    
    if role.startswith("-"):
        remove_user_role(target.id, role[1:])
        await message.reply(f"✅ Роль `{role[1:]}` снята с {target.first_name}", parse_mode="Markdown")
    else:
        if role not in _data["roles"]:
            return await message.reply(f"❌ Роль `{role}` не существует.", parse_mode="Markdown")
        add_user_role(target.id, role)
        await message.reply(f"✅ Роль `{role}` выдана {target.first_name}", parse_mode="Markdown")


@router.message(Command("rr"))
async def cmd_remove_role(message: types.Message):
    """Алиас для снятия роли"""
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Использование: /rr роль")
    
    target = message.reply_to_message.from_user
    role = args[1]
    remove_user_role(target.id, role)
    await message.reply(f"✅ Роль `{role}` снята с {target.first_name}", parse_mode="Markdown")


@router.message(Command("staff"))
async def cmd_staff(message: types.Message):
    staff = get_staff_list()
    if not staff:
        return await message.reply("👥 Персонала нет.")
    
    text = "👥 **Персонал чата:**\n\n"
    for member in staff:
        name = member["username"] or member["first_name"] or str(member["user_id"])
        roles = ", ".join(member["roles"])
        text += f"• {name} — `{roles}`\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("immunity"))
async def cmd_immunity(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только администраторы.")
    
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    roles = get_user_roles(target.id)
    if "immune" in roles:
        remove_user_role(target.id, "immune")
        await message.reply(f"🛡️ Иммунитет снят с {target.first_name}")
    else:
        add_user_role(target.id, "immune")
        await message.reply(f"🛡️ Иммунитет выдан {target.first_name}")


# ==================== ВАРНЫ ====================

@router.message(Command("warn"))
async def cmd_warn(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "warn"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    
    # Проверка иммунитета
    if "immune" in get_user_roles(target.id) and message.from_user.id not in ADMIN_IDS:
        return await message.reply("🛡️ У этого пользователя иммунитет.")
    
    create_user(target.id, target.username or "", target.first_name)
    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else "Без причины"
    
    total = add_warn(target.id, message.from_user.id, reason)
    await message.reply(f"⚠️ {target.first_name} получил варн (#{total})\nПричина: {reason}")


@router.message(Command("unwarn"))
async def cmd_unwarn(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "warn"):
        return await message.reply("❌ Недостаточно прав.")
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    args = message.text.split()
    warn_id = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    
    if remove_warn(target.id, warn_id):
        await message.reply(f"✅ Варн снят с {target.first_name}")
    else:
        await message.reply("❌ У пользователя нет варнов.")


@router.message(Command("warnlist"))
async def cmd_warnlist(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя.")
    
    target = message.reply_to_message.from_user
    warns = get_warns(target.id)
    
    if not warns:
        return await message.reply(f"✅ У {target.first_name} нет варнов.")
    
    text = f"⚠️ **Варны {target.first_name}:** {len(warns)}\n\n"
    for w in warns[-10:]:
        text += f"• #{w['id']} | {w['date']} | {w['reason']}\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("warnhistory"))
async def cmd_warnhistory(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "warn"):
        return await message.reply("❌ Недостаточно прав.")
    
    warns = _data["warn_history"][-20:]
    if not warns:
        return await message.reply("📝 История варнов пуста.")
    
    text = "📝 **Последние варны:**\n\n"
    for w in warns:
        text += f"• #{w['id']} | user:{w['user_id']} | {w['date']} | {w['reason']}\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("getwarn"))
async def cmd_getwarn(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Укажите ID варна: /getwarn 5")
    
    warn = get_warn_by_id(int(args[1]))
    if not warn:
        return await message.reply("❌ Варн не найден.")
    
    text = f"📋 **Варн #{warn['id']}**\n\n"
    text += f"👤 Пользователь: `{warn['user_id']}`\n"
    text += f"👮 Админ: `{warn['admin_id']}`\n"
    text += f"📅 Дата: {warn['date']}\n"
    text += f"📝 Причина: {warn['reason']}\n"
    text += f"🏷️ Тип: {warn['warn_type']}"
    await message.reply(text, parse_mode="Markdown")


# ==================== ФИЛЬТРЫ ====================

@router.message(Command("filteradd"))
async def cmd_filteradd(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "mute"):
        return await message.reply("❌ Недостаточно прав.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажите слово: /filteradd спам")
    
    add_filter_word(args[1])
    await message.reply(f"✅ Слово `{args[1]}` добавлено в фильтр.", parse_mode="Markdown")


@router.message(Command("filterdel"))
async def cmd_filterdel(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, "mute"):
        return await message.reply("❌ Недостаточно прав.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажите слово: /filterdel спам")
    
    if remove_filter_word(args[1]):
        await message.reply(f"✅ Слово `{args[1]}` удалено из фильтра.", parse_mode="Markdown")
    else:
        await message.reply("❌ Слово не найдено в фильтре.")


@router.message(Command("filter"))
@router.message(Command("filterlist"))
async def cmd_filterlist(message: types.Message):
    words = get_filter_words()
    if not words:
        return await message.reply("📝 Фильтр пуст.")
    
    text = "🚫 **Запрещённые слова:**\n"
    for i, word in enumerate(words, 1):
        text += f"{i}. `{word}`\n"
    await message.reply(text, parse_mode="Markdown")


# Автоматическая проверка сообщений
@router.message(F.text)
async def check_filters(message: types.Message):
    word = check_message_for_filters(message.text)
    if word and not is_admin_or_has_perm(message.from_user.id, ""):
        try:
            await message.delete()
            await message.answer(f"🚫 Сообщение удалено. Запрещённое слово.")
        except:
            pass


# ==================== ПРОФИЛЬ И ЭКОНОМИКА ====================

@router.message(Command("id"))
async def cmd_id(message: types.Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        await message.reply(f"🆔 ID {user.first_name}: `{user.id}`", parse_mode="Markdown")
    else:
        await message.reply(f"🆔 Ваш ID: `{message.from_user.id}`\n💬 Чат ID: `{message.chat.id}`", parse_mode="Markdown")


@router.message(Command("info"))
@router.message(Command("profile"))
async def cmd_profile(message: types.Message):
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    else:
        target = message.from_user
    
    create_user(target.id, target.username or "", target.first_name)
    user = get_user(target.id)
    roles = get_user_roles(target.id)
    
    text = f"👤 **Профиль {target.first_name}**\n\n"
    text += f"🆔 ID: `{target.id}`\n"
    text += f"💰 Баланс: {user['balance']} монет\n"
    text += f"⚠️ Варны: {user['warns']}\n"
    text += f"🔇 Замучен: {'Да' if user['is_muted'] else 'Нет'}\n"
    text += f"🚫 Забанен: {'Да' if user['is_banned'] else 'Нет'}\n"
    if roles:
        text += f"🎭 Роли: {', '.join(roles)}\n"
    
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name)
    user = get_user(message.from_user.id)
    await message.reply(f"💰 Ваш баланс: {user['balance']} монет")


@router.message(Command("daily"))
async def cmd_daily(message: types.Message):
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name)
    user = get_user(message.from_user.id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_daily"] == today:
        return await message.reply("❌ Вы уже получали ежедневную награду сегодня.")
    
    bonus = 100
    add_balance(message.from_user.id, bonus)
    update_user(message.from_user.id, last_daily=today)
    await message.reply(f"🎁 Вы получили {bonus} монет! Ежедневная награда.")


@router.message(Command("bonus"))
async def cmd_bonus(message: types.Message):
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name)
    user = get_user(message.from_user.id)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user["last_bonus"] == today:
        return await message.reply("❌ Вы уже получали бонус сегодня.")
    
    bonus = 50
    add_balance(message.from_user.id, bonus)
    update_user(message.from_user.id, last_bonus=today)
    await message.reply(f"🎉 Вы получили бонус {bonus} монет!")


@router.message(Command("pay"))
async def cmd_pay(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение пользователя для перевода.")
    
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        return await message.reply("❌ Укажите сумму: /pay 100")
    
    amount = int(args[1])
    if amount <= 0:
        return await message.reply("❌ Сумма должна быть положительной.")
    
    sender = message.from_user
    receiver = message.reply_to_message.from_user
    
    if sender.id == receiver.id:
        return await message.reply("❌ Нельзя перевести самому себе.")
    
    create_user(sender.id, sender.username or "", sender.first_name)
    create_user(receiver.id, receiver.username or "", receiver.first_name)
    
    sender_data = get_user(sender.id)
    if sender_data["balance"] < amount:
        return await message.reply("❌ Недостаточно средств.")
    
    add_balance(sender.id, -amount)
    add_balance(receiver.id, amount)
    
    await message.reply(f"💸 {sender.first_name} перевёл {amount} монет {receiver.first_name}")


@router.message(Command("top"))
async def cmd_top(message: types.Message):
    top = get_top_users(10)
    if not top:
        return await message.reply("📊 Рейтинг пуст.")
    
    text = "🏆 **Топ пользователей:**\n\n"
    for i, user in enumerate(top, 1):
        name = user["username"] or user["first_name"] or str(user["user_id"])
        text += f"{i}. {name} — {user['balance']} монет\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("work"))
@router.message(Command("works"))
async def cmd_work(message: types.Message):
    create_user(message.from_user.id, message.from_user.username or "", message.from_user.first_name)
    user = get_user(message.from_user.id)
    
    today = datetime.now().strftime("%Y-%m-%d %H")
    if user["last_work"].startswith(today[:13]):  # Проверка раз в час
        return await message.reply("❌ Вы уже работали в этом часе. Подождите.")
    
    import random
    jobs = ["курьером", "программистом", "поваром", "дизайнером", "охранником", "таксистом", "строителем"]
    earnings = random.randint(20, 80)
    
    add_balance(message.from_user.id, earnings)
    update_user(message.from_user.id, last_work=datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    await message.reply(f"💼 Вы поработали {random.choice(jobs)} и заработали {earnings} монет!")


# ==================== РЕПОРТЫ ====================

@router.message(Command("report"))
async def cmd_report(message: types.Message):
    if not message.reply_to_message:
        return await message.reply("❌ Ответьте на сообщение нарушителя.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажите причину: /report спам")
    
    target = message.reply_to_message.from_user
    ticket_id = create_ticket(message.from_user.id, f"Жалоба на {target.first_name}: {args[1]}")
    
    await message.reply(f"📩 Репорт #{ticket_id} создан. Администраторы рассмотрят его.")


@router.message(Command("tickets"))
async def cmd_tickets(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только для администраторов.")
    
    tickets = get_open_tickets()
    if not tickets:
        return await message.reply("📝 Нет открытых тикетов.")
    
    text = "📋 **Открытые тикеты:**\n\n"
    for t in tickets:
        text += f"• #{t['id']} | user:{t['user_id']} | {t['created_at']}\n  {t['subject']}\n\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("ticket"))
async def cmd_ticket(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Укажите ID тикета: /ticket 1")
    
    ticket = get_ticket(int(args[1]))
    if not ticket:
        return await message.reply("❌ Тикет не найден.")
    
    text = f"📩 **Тикет #{ticket['id']}**\n\n"
    text += f"👤 От: `{ticket['user_id']}`\n"
    text += f"📅 Дата: {ticket['created_at']}\n"
    text += f"📊 Статус: {ticket['status']}\n"
    text += f"📝 Тема: {ticket['subject']}"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("answer"))
async def cmd_answer(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только для администраторов.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Использование: /answer ID_тикета Ответ")
    
    parts = args[1].split(maxsplit=1)
    if len(parts) < 2 or not parts[0].isdigit():
        return await message.reply("❌ Формат: /answer 1 Ваш ответ")
    
    ticket = get_ticket(int(parts[0]))
    if not ticket:
        return await message.reply("❌ Тикет не найден.")
    
    await message.reply(f"📩 Ответ на тикет #{ticket['id']} отправлен.")
    # Здесь можно добавить отправку ответа пользователю


@router.message(Command("closeticket"))
async def cmd_closeticket(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только для администраторов.")
    
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Укажите ID тикета: /closeticket 1")
    
    if close_ticket(int(args[1])):
        await message.reply(f"✅ Тикет #{args[1]} закрыт.")
    else:
        await message.reply("❌ Тикет не найден.")


# ==================== СЕРВИС ====================

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    text = """🤖 **Помощь по командам:**

**Модерация:**
/mute, /unmute, /ban, /unban, /kick, /pin, /unpin, /delete, /cleanup

**Роли:**
/roles, /role, /rr, /staff, /immunity

**Варны:**
/warn, /unwarn, /warnlist, /warnhistory, /getwarn

**Фильтры:**
/filter, /filteradd, /filterdel, /filterlist

**Профиль и экономика:**
/id, /info, /profile, /balance, /daily, /bonus, /pay, /top, /work

**Репорты:**
/report, /tickets, /ticket, /answer, /closeticket

**Сервис:**
/help, /settings, /rules, /setrules, /welcome, /setwelcome"""
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    chat_id = message.chat.id
    welcome = get_chat_setting(chat_id, "welcome_text", "Не установлено")
    rules = get_chat_setting(chat_id, "rules_text", "Не установлены")
    
    text = f"⚙️ **Настройки чата:**\n\n"
    text += f"👋 Приветствие: {welcome[:100]}...\n" if len(welcome) > 100 else f"👋 Приветствие: {welcome}\n"
    text += f"📜 Правила: {rules[:100]}...\n" if len(rules) > 100 else f"📜 Правила: {rules}\n"
    await message.reply(text, parse_mode="Markdown")


@router.message(Command("rules"))
async def cmd_rules(message: types.Message):
    rules = get_chat_setting(message.chat.id, "rules_text", "Правила чата не установлены.")
    await message.reply(f"📜 **Правила чата:**\n\n{rules}", parse_mode="Markdown")


@router.message(Command("setrules"))
async def cmd_setrules(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только для администраторов.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажите текст правил.")
    
    set_chat_setting(message.chat.id, "rules_text", args[1])
    await message.reply("✅ Правила чата обновлены.")


@router.message(Command("welcome"))
async def cmd_welcome(message: types.Message):
    welcome = get_chat_setting(message.chat.id, "welcome_text", "Добро пожаловать, {user}!")
    await message.reply(f"👋 Текущее приветствие:\n{welcome}")


@router.message(Command("setwelcome"))
async def cmd_setwelcome(message: types.Message):
    if not is_admin_or_has_perm(message.from_user.id, ""):
        return await message.reply("❌ Только для админов нахуй.")
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply("❌ Укажите текст приветствия. Можно использовать {user}, {chat}, {id}")
    
    set_chat_setting(message.chat.id, "welcome_text", args[1])
    await message.reply("✅ Приветствие обновлено.")


# Приветствие новым участникам
@router.message(F.new_chat_members)
async def on_user_join(message: types.Message):
    for new_user in message.new_chat_members:
        create_user(new_user.id, new_user.username or "", new_user.first_name)
        welcome = get_chat_setting(message.chat.id, "welcome_text", "Добро пожаловать, {user}!")
        text = welcome.format(
            user=new_user.first_name,
            id=new_user.id,
            chat=message.chat.title,
        )
        await message.answer(text, parse_mode="HTML")