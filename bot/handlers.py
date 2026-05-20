from aiogram import F, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from django.utils import timezone
from asgiref.sync import sync_to_async
from main.models import User, WorkDay
from bot.keyboards import main_keyboard

async def start(message: Message):
    telegram_id = str(message.from_user.id)

    try:
        user = await sync_to_async(User.objects.get)(
            telegram_id=telegram_id
        )
    except User.DoesNotExist:
        await message.answer("Telegram не привязан.")
        return

    await message.answer("Выберите действие:", reply_markup=main_keyboard())


async def checkin(call: CallbackQuery):
    user = User.objects.get(telegram_id=str(call.from_user.id))

    work = await sync_to_async(
        lambda: WorkDay.objects.filter(
            user=user,
            is_active=True
        ).first()
    )()

    await sync_to_async(WorkDay.objects.create)(
        user=user
    )
    await call.message.answer("Приход отмечен ✅")

async def checkout(call: CallbackQuery):
    user = User.objects.get(telegram_id=str(call.from_user.id))

    work = WorkDay.objects.filter(user=user, is_active=True).first()

    if not work:
        await call.message.answer("Нет активной смены ❌")
        return

    work.end_time = timezone.now()
    work.is_active = False
    work.save()

    await call.message.answer(
        f"Закрыто 🚪\n"
        f"Часы: {work.get_hours()}\n"
        f"ЗП: {work.get_earnings()}"
    )

async def stats(message: Message):
    user = User.objects.get(telegram_id=str(message.from_user.id))

    days = WorkDay.objects.filter(user=user, is_active=False)

    total_hours = sum(d.get_hours() for d in days)
    total_money = sum(d.get_earnings() for d in days)

    await message.answer(
        f"📊 Статистика\n"
        f"Часы: {total_hours}\n"
        f"ЗП: {total_money}"
    )

def register_handlers(dp: Dispatcher):
    dp.message.register(start, Command("start"))
    dp.message.register(stats, Command("stats"))

    dp.callback_query.register(checkin, F.data == "checkin")
    dp.callback_query.register(checkout, F.data == "checkout")