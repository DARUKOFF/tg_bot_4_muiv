from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart

from settings import ADMIN_USER_IDS
from data.requests import get_operators_tg_ids, get_students_tg_ids
from keyboards import reply, inline


router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    OPERATORS = await get_operators_tg_ids()
    STUDENTS = await get_students_tg_ids()
    if user.id in ADMIN_USER_IDS:
        await message.answer(f'Добро пожаловать, администратор {user.first_name}!', reply_markup=reply.admin_main)
    elif user.id in OPERATORS:
        await message.answer(f'Добро пожаловать, оператор {user.first_name}!', reply_markup=reply.operator_main)
    elif user.id in STUDENTS:
        await message.answer(f'Добро пожаловать, {user.first_name}!', reply_markup=reply.student_main)
    else:
        await message.answer('Для начала работы с ботом необходимо пройти аутентификацию', reply_markup=inline.start_auth)


@router.callback_query(F.data == 'cancel_action')            
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await state.clear()
    OPERATORS = await get_operators_tg_ids()
    if callback.from_user.id in ADMIN_USER_IDS:
        reply_markup = reply.admin_main
    elif callback.from_user.id in OPERATORS:
        reply_markup = reply.operator_main
    else:
        reply_markup = reply.student_main
    await callback.message.answer(f'Действие отменено', reply_markup=reply_markup)

