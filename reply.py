from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

admin_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='⬇ Загрузить базу'), KeyboardButton(text='👨‍👦‍👦 Операторы')],
        [KeyboardButton(text='👨‍🎓👩‍🎓 Студенты'), KeyboardButton(text='📣 Рассылка')]],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...',
    selective=True,
    one_time_keyboard=True)

student_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='✍ Создать заявку')],
        [KeyboardButton(text='📃 Список заявок')]],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...',
    selective=True,
    one_time_keyboard=True)

operator_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🆕 Принятые'), KeyboardButton(text='⚙ В обработке')],
        [KeyboardButton(text='🏁 Завершённые (Архив)')]],
    resize_keyboard=True,
    input_field_placeholder='Выберите тип заявок...',
    selective=True,
    one_time_keyboard=True)

application_types = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📁 Документы'), KeyboardButton(text='⏳ Сроки')],
        [KeyboardButton(text='💲 Финансы')]],
    resize_keyboard=True,
    input_field_placeholder='Выберите категорию заявки...',
    selective=True,
    one_time_keyboard=True)

async def remove_kb():
    return ReplyKeyboardRemove()
