from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from contextlib import suppress
from datetime import datetime
from keyboards import reply, inline
from data.requests import (get_eligible_student_by_tg, set_student, set_application, get_operator_for_send, get_application_by_id, 
                           get_student_by_id, get_files_by_application_id, save_file, get_applications_by_student, 
                           get_operator_by_role)
from settings import TOKEN, COMMON_CHAT


class Authentification(StatesGroup):
    student_id = State()


class Application(StatesGroup):
    student_id = State()
    operator_id = State()
    category = State()
    text = State()
    start_date = State()


class ApplicationFiles(StatesGroup):
    application_id = State()
    files = State()


router = Router()

@router.callback_query(F.data == 'start_auth')
async def start_auth(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Введите номер Вашего студенческого билета')
    await state.set_state(Authentification.student_id)


@router.message(Authentification.student_id)
async def authentificate(message: Message, state: FSMContext):
    student_id = message.text
    if await set_student(student_id, message.from_user.id):
        await message.answer('Аутентификация прошла успешно', reply_markup=reply.student_main)
        await state.clear()
    else:
        await message.answer('Проверьте правильность ввода номера студенческого билета, или обратитесь к '
                             'администратору с просьбой добавить Вас в базу данных')
        

@router.message(F.text == '✍ Создать заявку')
async def create_application(message: Message, state: FSMContext):
    student = await get_eligible_student_by_tg(message.from_user.id)
    if student:
        await state.update_data(student_id=student.id)
        await message.answer('Выберите категорию заявки', reply_markup=reply.application_types)
        await state.set_state(Application.operator_id)
    else:
        await message.answer(f'Вы не прошли аутентификацию. \n\nНажмите /start', reply_markup=await reply.remove_kb())


@router.message(Application.operator_id)
async def application_category(message: Message, state: FSMContext):
    if message.text == '📁 Документы':
        category = 'documents'
    elif message.text == '⏳ Сроки':
        category = 'terms'
    elif message.text == '💲 Финансы':
        category = 'finances'
    else:
        await message.answer('Выберите категорию заявки', reply_markup=reply.application_types)
        return
    operator = await get_operator_by_role(category)
    await state.update_data(operator_id=operator.id)
    await state.update_data(category=category)
    await message.answer('Введите текст заявки', reply_markup=inline.cancel_action)
    await state.set_state(Application.text)


@router.message(Application.text)
async def application_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    now_str = datetime.now().strftime(f"%Y.%m.%d %H:%M:%S")
    now = datetime.strptime(now_str, f"%Y.%m.%d %H:%M:%S")
    await state.update_data(start_date=now)
    data = await state.get_data()
    await state.clear()
    application_id = await set_application(data)
    guide = ('Для отправки документов и архивов нажмите на знак скрепки и выберите "Документ"(если на смартфоне - то "Файл"). '
             'Для отправки фото/видео файлов нажмите на знак скрепки и выберите "Фото или Видео"(на смартфоне выберите '
             'медиафайл из галереи). Для отправки аудиофайла со смартфона выберите нажмите на знак скрепки и выберите "Музыки"')
    await message.answer(f'Прикрепите файлы по одному или нажмите кнопку для отправки заявки без файлов\n\n{guide}', 
                         reply_markup=await inline.send_now(application_id))
    await state.update_data(application_id=application_id)
    await state.set_state(ApplicationFiles.files)


@router.message(ApplicationFiles.files)
async def handle_files(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.document:
        await save_file('document', message.document.file_id, data['application_id'])
    elif message.photo:
        await save_file('photo', message.photo[-1].file_id, data['application_id'])
    elif message.audio:
        await save_file('audio', message.audio.file_id, data['application_id'])
    elif message.video:
        await save_file('video', message.video.file_id, data['application_id'])
    else:
        await message.answer('Неизвестный тип файла')
    await message.answer(f'Вы можете прикрепить еще файлы или отправить заявку прямо сейчас',
                        reply_markup=await inline.send_now(data['application_id']))


@router.callback_query(F.data.startswith('application_now_'))
async def finalize_application(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    application_id = callback.data.split('_')[2]
    await send_application(application_id, bot)
    await callback.message.delete_reply_markup()
    await callback.message.answer('Ваша заявка отправлена!', reply_markup=reply.student_main)


async def send_application(application_id, bot):
    application = await get_application_by_id(application_id)
    operator = await get_operator_for_send(application.operator_id)
    student = await get_student_by_id(application.student_id)
    gender = 'Студентки' if 'овна' in student.full_name else 'Студента'
    
    files = await get_files_by_application_id(application.id)
    files_warn = 'Приложенные файлы:' if len(files) > 0 else ''
    application_message = (
        f"{application.start_date}\n\n"
        f"Заявка №{application.id} от {gender}:\n"
        f"{student.full_name}\nТелефон: {student.phone_number}\nСтуд. билет: {student.student_id}\nГруппа: {student.group_id}"
        f"\n\nКатегория: {application.category}\nТекст: {application.text}\n\n"
        f"Статус: 🆕<b>Принята</b>🆕\n\nНажмите кнопку ниже для отправки ответа. Статус завяки изменится автоматически"
        f"\n\n{files_warn}"
    )
    with suppress(TelegramForbiddenError, TelegramBadRequest):
        await bot.send_message(operator.tg_id, application_message, 
                               reply_markup=await inline.start_answer(application.id))
    await bot.send_message(COMMON_CHAT, application_message)
     
    if len(files) > 0:
        await send_application_files(application.id, operator.tg_id, files, bot)

async def send_application_files(application, operator, files, bot):
    # bot = Bot(token=TOKEN)
    # bot.default.parse_mode = 'HTML'
    for ifile in files:
        try:
            if ifile.file_type == 'document':
                await bot.send_document(operator, document=ifile.file_id, 
                                        caption=f'К заявке №{application} прикреплён документ')
            elif ifile.file_type == 'photo':
                await bot.send_photo(operator, photo=ifile.file_id,
                                        caption=f'К заявке №{application} прикреплено фото')
            elif ifile.file_type == 'audio':
                await bot.send_audio(operator, audio=ifile.file_id,
                                    caption=f'К заявке №{application} прикреплено аудио')
            elif ifile.file_type == 'video':
                await bot.send_video(operator, video=ifile.file_id,
                                    caption=f'К заявке №{application} прикреплено видео')
        except Exception as e:
            print(f'Не удалось отправить заявку оператору с ID: {operator} из-за ошибки:\n{e}')
    # await bot.session.close()
        

@router.message(F.text == '📃 Список заявок')
async def list_applications(message: Message):
    student = await get_eligible_student_by_tg(message.from_user.id)
    if student:
        applications = await get_applications_by_student(student.id)
        apps_info = "\n".join([f'{app.id}\nПринята: {app.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}'
                            f'\nЗавершена: {app.finish_date.strftime(f"%Y.%m.%d %H:%M:%S") if app.finish_date else None}'
                            f'\n{app.text}\n<b>⚪{app.status}⚪</b>' for app in applications])
        if len(apps_info) > 1:
            await message.answer(f'Ваши заявки:\n\n{apps_info}', reply_markup=inline.cancel_action)
        else:
            await message.answer('У вас нет заявок')
    else:
        await message.answer(f'Вы не прошли аутентификацию. \n\nНажмите /start', reply_markup=await reply.remove_kb())


@router.message()
async def unknown_command(message: Message):
    if message.chat.type not in ['group', 'supergroup']:
        await message.answer('Неизвестная команда')
