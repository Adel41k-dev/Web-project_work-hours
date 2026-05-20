import asyncio
import os
import django
from django.utils import timezone
from datetime import timedelta
from datetime import datetime, timedelta
import calendar
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from aiogram.types import BotCommand


def get_day_range(now):
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


def get_week_range(now):
    start = now - timedelta(days=now.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return start, end


def get_month_range(now):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = calendar.monthrange(now.year, now.month)[1]
    end = start + timedelta(days=last_day)
    return start, end




# ---------------- DJANGO INIT ----------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "work_hour.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from main.models import WorkDay

User = get_user_model()

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запуск бота"),
        BotCommand(command="users", description="👥 Все пользователи (админ)"),
        BotCommand(command="active", description="🟢 Активные пользователи (админ)"),
        BotCommand(command="stats", description="📊 Статистика"),
    ]

    await bot.set_my_commands(commands)

# ---------------- ADMIN CHECK ----------------
def is_admin(tg_id):
    return str(tg_id) == str(settings.ADMIN_TELEGRAM_ID)


# ---------------- GET USER ----------------
async def get_user(tg_id: str):
    return await sync_to_async(
        lambda: User.objects.filter(telegram_id=tg_id).first()
    )()


# ---------------- KEYBOARDS ----------------
def user_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Начать", callback_data="checkin"),
            InlineKeyboardButton(text="🔴 Завершить", callback_data="checkout"),
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
        ]
    ])


def admin_users_keyboard(users):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=u.username, callback_data=f"USER|{u.id}")]
        for u in users
    ])


def period_keyboard(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 День", callback_data=f"STAT|DAY|{user_id}"),
            InlineKeyboardButton(text="📆 Неделя", callback_data=f"STAT|WEEK|{user_id}")
        ],
        [
            InlineKeyboardButton(text="🗓 Месяц", callback_data=f"STAT|MONTH|{user_id}")
        ]
    ])


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: Message):

    tg_id = message.from_user.id

    if is_admin(tg_id):
        await message.answer(
            "👑 Админ режим\n\n"
            "/users - все пользователи\n"
            "/active - активные\n"
            "/stats_admin - статистика"
        )
        return

    user = await get_user(str(tg_id))

    if not user:
        await message.answer("❌ Нет доступа")
        return

    await message.answer(
        f"👋 {user.username}",
        reply_markup=user_keyboard()
    )

    #  уведомление админу
    if not is_admin(message.from_user.id):
        await bot.send_message(
            settings.ADMIN_TELEGRAM_ID,
            f"🔔 Вход в аккаунт\n\n"
            f"👤 Пользователь: {user.username}\n"
            f"🆔 TG ID: {user.telegram_id}"
        )


# =========================
# 👤 USER FUNCTIONS
# =========================

@dp.message(Command("checkin"))
async def checkin_cmd(message: Message):

    user = await sync_to_async(
        lambda: User.objects.filter(telegram_id=str(message.from_user.id)).first()
    )()

    if not user:
        await message.answer("❌ Нет доступа")
        return

    active = await sync_to_async(
        lambda: WorkDay.objects.filter(user=user, is_active=True).exists()
    )()

    if active:
        await message.answer("⚠️ У вас уже идёт рабочая сессия")
        return

    await sync_to_async(WorkDay.objects.create)(
        user=user,
        start_time=timezone.now(),
        is_active=True
    )

    await message.answer("🟢 День начат")
    if not is_admin(message.from_user.id):
        await bot.send_message(
            settings.ADMIN_TELEGRAM_ID,
            f"🟢 Начало рабочего дня\n\n"
            f"👤 {user.username}\n"
            f"🆔 {user.telegram_id}\n"
            f"🕒 {timezone.now()}"
        )


@dp.message(Command("checkout"))
async def checkout_cmd(message: Message):

    user = await sync_to_async(
        lambda: User.objects.filter(telegram_id=str(message.from_user.id)).first()
    )()

    if not user:
        await message.answer("❌ Нет доступа")
        return

    work = await sync_to_async(
        lambda: WorkDay.objects.filter(user=user, is_active=True).first()
    )()

    if not work:
        await message.answer("⚠️ Нет активной смены")
        return

    work.end_time = timezone.now()
    work.is_active = False
    await sync_to_async(work.save)()

    hours = work.get_hours()
    money = hours * user.hourly_rate

    await message.answer(
        "🔴 День завершён\n\n"
        f"⏱ Часы: {round(hours, 2)}\n"
        f"💰 Зарплата: {round(money, 2)}"
    )

@dp.message(Command("stats"))
async def stats_cmd(message: Message):

    user = await sync_to_async(
        lambda: User.objects.filter(telegram_id=str(message.from_user.id)).first()
    )()

    if not user:
        await message.answer("❌ Аккаунт не привязан")
        return

    now = timezone.now()

    workdays = await sync_to_async(
        lambda: list(
            WorkDay.objects.filter(
                user=user,
                is_active=False,
                start_time__date=now.date()
            )
        )
    )()

    total_hours = sum(w.get_hours() for w in workdays)
    total_money = total_hours * user.hourly_rate

    await message.answer(
        f"📊 Статистика\n\n"
        f"⏱ {round(total_hours, 2)} часов\n"
        f"💰 {round(total_money, 2)}"
    )

# =========================
# 👑 ADMIN FUNCTIONS
# =========================

# 👥 USERS LIST
@dp.message(Command("users"))
async def users(message: Message):

    if not is_admin(message.from_user.id):
        return

    users = await sync_to_async(
        lambda: list(
            User.objects.filter(
                is_staff=False,
                is_superuser=False
            )
        )
    )()

    if not users:
        await message.answer("❌ Пользователей нет")
        return

    text = "👥 Список пользователей:\n\n"

    for u in users:
        text += (
            f"👤 {u.username}\n"
            f"🆔 TG ID: {u.telegram_id}\n\n"
        )

    await message.answer(text)


# 🟢 ACTIVE USERS
@dp.message(Command("active"))
async def active(message: Message):

    if not is_admin(message.from_user.id):
        return

    active = await sync_to_async(
        lambda: list(
            WorkDay.objects.filter(is_active=True).select_related("user")
        )
    )()

    if not active:
        await message.answer("⚠️ Никто не работает")
        return

    text = "🟢 Активные:\n\n"
    for w in active:
        text += f"- {w.user.username} | {w.start_time}\n"

    await message.answer(text)


# 📊 ADMIN STATS START
@dp.message(Command("stats_admin"))
async def admin_stats(message: Message):

    if not is_admin(message.from_user.id):
        return

    users = await sync_to_async(
        lambda: list(
            User.objects.filter(
                is_staff=False,
                is_superuser=False
            )
        )
    )()

    await message.answer(
        "👥 Выбери пользователя:",
        reply_markup=admin_users_keyboard(users)
    )


# 👤 USER SELECT
@dp.callback_query(F.data.startswith("USER|"))
async def select_user(call: CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    user_id = call.data.split("|")[1]

    await call.message.answer(
        "⏱ Выбери период:",
        reply_markup=period_keyboard(user_id)
    )


# 📊 PERIOD STATS (ФИНАЛЬНО ИСПРАВЛЕНО)
@dp.callback_query(F.data.startswith("STAT|"))
async def period_stats(call: CallbackQuery):

    if not is_admin(call.from_user.id):
        return

    try:
        _, period, user_id = call.data.split("|")
    except:
        await call.message.answer("❌ Ошибка callback")
        return

    user = await sync_to_async(
        lambda: User.objects.filter(id=user_id).first()
    )()

    if not user:
        await call.message.answer("❌ Пользователь не найден")
        return

    now = timezone.now()

    if period == "DAY":
        start, end = get_day_range(now)
    elif period == "WEEK":
        start, end = get_week_range(now)
    else:
        start, end = get_month_range(now)

    workdays = await sync_to_async(
        lambda: list(
            WorkDay.objects.filter(
                user=user,
                start_time__gte=start,
                start_time__lt=end
            ).select_related("user")
        )
    )()

    if not workdays:
        await call.message.answer("📊 Нет данных за период")
        return

    total_hours = 0
    total_money = 0

    for w in workdays:
        hours = w.get_hours()
        total_hours += hours
        total_money += hours * user.hourly_rate

    await call.message.answer(
        "📊 Статистика\n\n"
        f"👤 {user.username}\n"
        f"⏱ Часы: {round(total_hours, 2)}\n"
        f"💰 Зарплата: {round(total_money, 2)}\n"
        f"📅 Записей: {len(workdays)}"
    )

admin_commands = [
    BotCommand(command="start", description="🚀 Запуск бота"),
    BotCommand(command="stats_admin", description="📊 Статистика"),
    BotCommand(command="users", description="👥 Пользователи"),
    BotCommand(command="active", description="🟢 Активные"),
]

from aiogram.types import BotCommandScopeChat

async def set_commands(bot: Bot):

    # ❗ очистить старые (ВАЖНО)
    await bot.delete_my_commands(scope=BotCommandScopeDefault())

    # 👤 user меню
    await bot.set_my_commands(
        user_commands,
        scope=BotCommandScopeDefault()
    )

    # 👑 admin меню
    await bot.set_my_commands(
        admin_commands,
        scope=BotCommandScopeChat(chat_id=int(settings.ADMIN_TELEGRAM_ID))
    )
from aiogram.types import BotCommandScopeDefault, BotCommand

user_commands = [
    BotCommand(command="start", description="🚀 Запуск бота"),
    BotCommand(command="checkin", description="🟢 Начать день"),
    BotCommand(command="checkout", description="🔴 Закончить день"),
    BotCommand(command="stats", description="📊 Статистика"),
]

# ---------------- START BOT ----------------
async def main():
    await set_commands(bot)
    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())
