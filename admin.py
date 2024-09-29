from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramForbiddenError

import openpyxl
import aiofiles
import aiohttp
import os
from contextlib import suppress

from keyboards import reply, inline
from filters.is_admin import IsAdmin
from data.requests import (get_students, set_operator, check_role, get_eligible_operators, edit_operator, change_operator,
                           get_operator_by_id, get_student_by_id, edit_student, save_from_xlsx, get_uneligible_operators)
from settings import TOKEN


router = Router()

class Newsletter(StatesGroup):
    message = State()
    

class DownloadBase(StatesGroup):
    base_file = State()


class EditStudent(StatesGroup):
    student_id = State()


class EditOperator(StatesGroup):
    action = State()
    operator_id = State()
    role = State()


@router.message(IsAdmin(), F.text == '👨‍👦‍👦 Операторы')
async def operators_menu(message: Message):
    await message.answer('Выберите что нужно сделать с операторами', reply_markup=inline.operators_menu)


@router.callback_query(F.data.startswith('new_operator_'))
async def new_operator_selected(callback: CallbackQuery, bot: Bot):
    role = callback.data.split('_')[2]
    operator_tg_id = callback.data.split('_')[3]
    operator_username = callback.data.split('_')[4]
    await handle_operator_assignment(role, operator_tg_id, operator_username, callback, bot)

@router.callback_query(F.data.startswith('change_operator_'))
async def change_operator_selected(callback: CallbackQuery, bot: Bot):
    role = callback.data.split('_')[2]
    operator_tg_id = callback.data.split('_')[3]
    operator_username = callback.data.split('_')[4]
    await handle_operator_assignment(role, operator_tg_id, operator_username, callback, bot, is_change=True)


async def handle_operator_assignment(role, operator_tg_id, operator_username, callback, bot, is_change=False):
    role_translate = translate_role(role)
    
    if not is_change:
        old_operator = await check_role(role)
        if old_operator is None:
            await set_operator(role, operator_tg_id, operator_username)
            await bot.send_message(operator_tg_id, f'Вы назначены на {role_translate}')
            await callback.message.delete_reply_markup()
            await callback.message.answer(f'Оператор успешно назначен на {role_translate}', reply_markup=reply.admin_main)
        else:
            await callback.message.edit_text('Этот оператор уже назначен. Хотите ли Вы заменить его?',
                                              reply_markup=await inline.change_operator(role, operator_tg_id, operator_username))
    else:
        await change_operator(role, operator_tg_id, operator_username)
        await bot.send_message(operator_tg_id, f'Вы назначены на {role_translate}')
        await callback.message.delete_reply_markup()
        await callback.message.answer(f'Оператор успешно назначен на {role_translate}', reply_markup=reply.admin_main)


def translate_role(role):
    translations = {
        'documents': 'Документы',
        'terms': 'Сроки',
        'finances': 'Финансы'
    }
    return translations.get(role, 'Неизвестная роль')


@router.callback_query(F.data.startswith('edit_operator_'))
async def edit_operator_selected(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[2]
    await state.update_data(action=action)
    if action == 'restrict':
        operators = await get_eligible_operators()
        text_action = 'ограничения доступа'
    elif action == 'restore':
        operators = await get_uneligible_operators()
        text_action = 'восстановления доступа'
    else:
        operators = await get_eligible_operators()
        text_action = 'назначения на другую роль'
    operators_info  = "\n".join([f'{operator.id} - @{operator.username}' for operator in operators])
    await callback.message.edit_text(f'{operators_info}\n\nВведите ID оператора для его {text_action}', 
                                     reply_markup=inline.cancel_action)
    await state.set_state(EditOperator.operator_id)


@router.message(EditOperator.operator_id)
async def apply_operator_status(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(operator_id=message.text)
    data = await state.get_data()
    action = data.get('action')
    operator_id = message.text
    operator = await get_operator_by_id(operator_id)
    if operator is None:
        await message.answer('Введённый id не найден. Проверьте данные и повторите попытку', reply_markup=inline.cancel_action)
        return
    else:
        if action in ('restrict', 'restore'):
            result = 'ограничен' if action == 'restrict' else 'восстановлен'
            await edit_operator(operator_id, action)
            await message.answer(f'Доступ оператора @{operator.username} был {result}', reply_markup=reply.admin_main)
            await bot.send_message(operator.tg_id, f'Ваша доступ был {result}')
            await state.clear() 
        else:
            await message.answer(f'Выберите новую роль для оператора @{operator.username}', reply_markup=reply.application_types)
            await state.set_state(EditOperator.role)
        

@router.message(EditOperator.role)
async def apply_role_operator(message: Message, state: FSMContext, bot: Bot):
    roles = {
        '📁 Документы': 'documents',
        '⏳ Сроки': 'terms',
        '💲 Финансы': 'finances'
    }
    role = roles.get(message.text)
    role_translate = translate_role(role)
    data = await state.get_data()
    await state.clear()
    operator_id = data['operator_id']
    operator = await get_operator_by_id(operator_id)
    await edit_operator(operator_id, 'role', role)
    await message.answer(f'Оператор {operator.username} успешно назначен на {role_translate}', reply_markup=reply.admin_main)
    await bot.send_message(operator.tg_id, f'Вы назначены на {role_translate}')


@router.message(IsAdmin(), F.text == '👨‍🎓👩‍🎓 Студенты')
async def students_menu(message: Message):
    await message.answer('Выберите что нужно сделать со студентами', reply_markup=inline.students_menu)


@router.callback_query(F.data.startswith('students_'))
async def students_selected(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    await state.update_data(action=action)
    students = await get_students()
    student_info = "\n".join([f'{student.id} - {student.student_id} - {student.full_name}' for student in students])
    await callback.message.edit_text(f'{student_info}\n\nВведите ID студента',
                                     reply_markup=inline.cancel_action)
    await state.set_state(EditStudent.student_id)


@router.message(EditStudent.student_id)
async def finish_edit_student(message: Message, state: FSMContext, bot: Bot):
    student_id = message.text
    student = await get_student_by_id(student_id)
    data = await state.get_data()
    gender = 'Студентка' if 'овна' in student.full_name else 'Студент'
    text_action = 'ограничен в доступе' if data.get('action') == 'restrict' else 'восстановлен в доступе'
    text_action_for_student = 'ограничен' if data.get('action') == 'restrict' else 'восстановлен'
    await state.clear()
    if student:
        await edit_student(student_id, data['action'])
        await message.answer(f'{gender} {student.full_name} успешно {text_action}', reply_markup=reply.admin_main)
        try:
            await bot.send_message(student.tg_id, f'Ваш доступ к боту был {text_action_for_student}')
        except Exception as e:
            print(e)
    else:
        await message.answer('Введённый id не найден. Проверьте данные и повторите попытку', reply_markup=inline.cancel_action)
        return


@router.message(IsAdmin(), F.text == '⬇ Загрузить базу')
async def start_download_base(message: Message, state: FSMContext):
    await state.set_state(DownloadBase.base_file)
    await message.answer('Отправьте файл в формате .xlsx', reply_markup=inline.cancel_action)


@router.message(IsAdmin(), F.document)
async def handle_file_upload(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    document = message.document
    file_id = document.file_id
    file_path = await bot.get_file(file_id)
    file_link = f"https://api.telegram.org/file/bot{TOKEN}/{file_path.file_path}"
    await message.answer('База загружается...')
    await download_excel_file(message, file_link)
    await message.answer('База успешно загружена', reply_markup=reply.admin_main)


async def download_excel_file(message: Message, file_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                local_file_path = "downloaded_file.xlsx"
                async with aiofiles.open(local_file_path, mode='wb') as out_file:
                    content = await response.read()
                    await out_file.write(content)

                await process_excel_file(local_file_path)
                os.remove(local_file_path)
            else:
                await message.answer(f"Ошибка загрузки файла: {response.status}")

async def process_excel_file(file):
    workbook = openpyxl.load_workbook(filename=file)
    sheet = workbook.active

    full_name_index = 1
    group_id_index = 2
    student_id_index = 3
    phone_number_index = 4

    for row in sheet.iter_rows(min_row=3, values_only=True):
        full_name = row[full_name_index]
        group_id = row[group_id_index]
        student_id = row[student_id_index]
        phone_number = row[phone_number_index]

        await save_from_xlsx(full_name, group_id, student_id, phone_number)


@router.message(IsAdmin(), F.text == '📣 Рассылка')
async def start_newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.message)
    await message.answer('Введите текст рассылки', reply_markup=inline.cancel_action)


@router.message(IsAdmin(), Newsletter.message)
async def send_newsletter(message: Message, state: FSMContext):
    await state.clear()
    students = await get_students()
    for student in students:
        if student.tg_id:
            with suppress(TelegramForbiddenError):
                await message.send_copy(chat_id=student.tg_id)
    await message.answer('Рассылка успешно завершена', reply_markup=reply.admin_main)
