from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from settings import ADMIN_USER_IDS
from keyboards import inline, reply
from data.requests import (get_application_by_id, get_student_by_id, change_application_status, get_files_by_application_id,
                           get_applications_by_status_and_operator, save_answer_file, save_answer, get_files_by_answer_id,
                           get_answer_by_id)

router = Router()


class OperatorAnswer(StatesGroup):
    application_id = State()
    answer_id = State()
    files = State()
    

@router.callback_query(F.data.startswith("start_answer_"))
async def answer_selected(callback: CallbackQuery, state: FSMContext, bot: Bot):
    application_id = callback.data.split('_')[2]
    application = await get_application_by_id(application_id)
    await change_application_status(application_id, 'process')
    student = await get_student_by_id(application.student_id)
    await bot.send_message(student.tg_id, f'Ваша заявка №{application.id} принята в работу')
    student_sex = 'Студентки' if 'овна' in student.full_name else 'Студента'
    files = await get_files_by_application_id(application.id)
    files_warn = 'Приложенные файлы' if len(files) > 0 else ''
    await callback.message.edit_text(f'{application.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}\n\nЗаявка №{application.id} '
        f'от {student_sex}:\n{student.full_name}\nТелефон: {student.phone_number}\nСтуд. билет: {student.student_id}\nГруппа: '
        f'{student.group_id}\n\nКатегория: {application.category}\nТекст: {application.text}\n\n{files_warn}\n\nСтатус: '
        f'⚙️<b>В обработке</b>⚙️\n\n', reply_markup=await inline.start_answer(application_id))
    await state.update_data(application_id=application_id)
    await callback.message.delete_reply_markup()
    await callback.message.answer(f'Напишите Ваш ответ на заявку №{application.id}')
    await state.set_state(OperatorAnswer.answer_id)


@router.message(OperatorAnswer.answer_id)
async def handle_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    answer_text = message.text
    if message.text:
        answer_id = await save_answer(answer_text, data['application_id'])
        await state.update_data(answer_id=answer_id)
        guide = ('Для отправки документов и архивов нажмите на знак скрепки и выберите "Документ"(если на смартфоне - то "Файл"). '
             'Для отправки фото/видео файлов нажмите на знак скрепки и выберите "Фото или Видео"(на смартфоне выберите '
             'медиафайл из галереи). Для отправки аудиофайла со смартфона выберите нажмите на знак скрепки и выберите "Музыки"')
        await message.answer(f'Прикрепите файлы по одному или нажмите кнопку для отправки ответа без файлов\n\n{guide}',
                              reply_markup=await inline.send_answer_now(data['application_id'], answer_id))
        await state.set_state(OperatorAnswer.files)
    else:
        await message.answer('Пожалуйста, введите текст ответа')
        return


@router.message(OperatorAnswer.files)
async def handle_answer_files(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.document:
        await save_answer_file('document', message.document.file_id, data['answer_id'])
    elif message.photo:
        await save_answer_file('photo', message.photo[-1].file_id, data['answer_id'])
    elif message.audio:
        await save_answer_file('audio', message.audio.file_id, data['answer_id'])
    elif message.video:
        await save_answer_file('video', message.video.file_id, data['answer_id'])
    else:
        await message.answer('Неизвестный тип файла')
    await message.answer(f'Вы можете прикрепить еще файлы или отправить ответ прямо сейчас',
                            reply_markup=await inline.send_answer_now(data['application_id'], data['answer_id']))
    

@router.callback_query(F.data.startswith("answer_now_"))
async def finalize_answer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    application_id = callback.data.split('_')[2]
    answer_id = callback.data.split('_')[3]
    await send_answer(callback, application_id, answer_id, bot)
    await callback.message.answer('Ответ отправлен', reply_markup=reply.operator_main)

async def send_answer(callback: CallbackQuery, application_id, answer_id, bot: Bot):
    application = await get_application_by_id(application_id)
    answer = await get_answer_by_id(answer_id)
    await change_application_status(application_id, 'completed', answer_id)
    student = await get_student_by_id(application.student_id)
    student_sex = 'Студентки' if 'овна' in student.full_name else 'Студента'
    files = await get_files_by_answer_id(answer.id)
    files_warn = 'Приложенные файлы' if len(files) > 0 else ''
    await callback.message.edit_text(f'{application.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}\n\nЗаявка №{application.id} '
        f'от {student_sex}:\n{student.full_name}\nТелефон: {student.phone_number}\nСтуд. билет: {student.student_id}\nГруппа: '
        f'{student.group_id}\n\nКатегория: {application.category}\nТекст: {application.text}\n\nСтатус: 🏁<b>Выполнена</b>🏁\n\n'
        f'Вашт ответ: {answer.text}')
    await bot.send_message(student.tg_id, f'Заявка №{application.id} от {application.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}'
        f'\nТекст: {application.text}\n\nОтвет оператора:{answer.text}\n\nСтатус: 🏁<b>Выполнена</b>🏁\n\n{files_warn}')
    if len(files) > 0:
        await send_answer_files(application.id, student, files, bot)


async def send_answer_files(application, student, files, bot):
    for ifile in files:
        try:
            if ifile.answer_file_type == 'document':
                await bot.send_document(student.tg_id, document=ifile.answer_file_id, 
                                        caption=f'К ответу по заявке №{application} прикреплён документ')
            elif ifile.answer_file_type == 'photo':
                await bot.send_photo(student.tg_id, photo=ifile.answer_file_id,
                                        caption=f'К ответу по заявке №{application} прикреплено фото')
            elif ifile.answer_file_type == 'audio':
                await bot.send_audio(student.tg_id, audio=ifile.answer_file_id,
                                    caption=f'К ответу по заявке №{application} прикреплено аудио')
            elif ifile.answer_file_type == 'video':
                await bot.send_video(student.tg_id, video=ifile.answer_file_id,
                                    caption=f'К ответу по заявке №{application} прикреплено видео')
        except Exception as e:
            print(f'Не удалось отправить ответ студенту {student.username} из-за ошибки:\n{e}')
            

@router.message(F.text == "🆕 Принятые")
async def applied(message: Message):
    applications = await get_applications_by_status_and_operator('applied', message.from_user.id)
    apps_info = "\n".join([f'{app.id}\nПринята: {app.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}'
                            f'\nЗавершена: {app.finish_date.strftime(f"%Y.%m.%d %H:%M:%S") if app.finish_date else None}'
                            f'\n{app.text}\n<b>🆕{app.status}🆕</b>' for app in applications])
    if len(apps_info) > 1:
        await message.answer(f'Принятые заявки:\n\n{apps_info}', reply_markup=reply.operator_main)
    else:
        await message.answer('У вас нет заявок')


@router.message(F.text == "⚙ В обработке")
async def in_process(message: Message):
    applications = await get_applications_by_status_and_operator('process', message.from_user.id)
    apps_info = "\n".join([f'{app.id}\nПринята: {app.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}'
                            f'\nЗавершена: {app.finish_date.strftime(f"%Y.%m.%d %H:%M:%S") if app.finish_date else None}'
                            f'\n{app.text}\n⚙️<b>{app.status}</b>⚙️' for app in applications])
    if len(apps_info) > 1:
        await message.answer(f'Заявки в обработке:\n\n{apps_info}', reply_markup=reply.operator_main)
    else:
        await message.answer('У вас нет заявок')


@router.message(F.text == "🏁 Завершённые (Архив)")
async def completed(message: Message):
    applications = await get_applications_by_status_and_operator('completed', message.from_user.id)
    apps_info = "\n".join([f'{app.id}\nПринята: {app.start_date.strftime(f"%Y.%m.%d %H:%M:%S")}'
                            f'\nЗавершена: {app.finish_date.strftime(f"%Y.%m.%d %H:%M:%S") if app.finish_date else None}'
                            f'\n{app.text}\n<b>🏁{app.status}🏁</b>' for app in applications])
    if len(apps_info) > 1:
        await message.answer(f'Завершённые заявки:\n\n{apps_info}', reply_markup=reply.operator_main)
    else:
        await message.answer('У вас нет заявок')


@router.message(F.text == "Operator2024")
async def operator_start(message: Message, bot: Bot):
    user = message.from_user
    user_link = f"<a href='tg://user?id={user.id}'>{user.full_name if len(user.full_name) > 1 else user.username}</a>"
    for admin in ADMIN_USER_IDS:
        await bot.send_message(admin, f"Новая заявка на оператора от пользователя {user_link}", 
                               reply_markup=await inline.choose_role(user.id, user.username))
    await message.answer("Ваша заявка отправлена администратору. Скоро Вы получите сообщение с результатом ей рассмотрения")
