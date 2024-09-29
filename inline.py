from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


start_auth = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🤝 Авторизоваться', callback_data='start_auth')]
    ]
)

cancel_action = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
    ]
)

operators_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🛑 Ограничить доступ', callback_data='edit_operator_restrict')],
        [InlineKeyboardButton(text='✔ Восстановить доступ', callback_data='edit_operator_restore')],
        [InlineKeyboardButton(text='🔄 Изменить роль', callback_data='edit_operator__role')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
    ]
)

students_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🛑 Ограничить доступ', callback_data='students_restrict')],
        [InlineKeyboardButton(text='✔ Восстановить доступ', callback_data='students_restore')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
    ]
)

async def send_now(application_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📤 Отправить заявку', callback_data=f'application_now_{application_id}'),
            InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
        ]
)


async def choose_role(user_id, username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
             [InlineKeyboardButton(text='📁 Документы', callback_data=f'new_operator_documents_{user_id}_{username}')],
             [InlineKeyboardButton(text='⏳ Сроки', callback_data=f'new_operator_terms_{user_id}_{username}')],
             [InlineKeyboardButton(text='💲 Финансы', callback_data=f'new_operator_finances_{user_id}_{username}')],
             [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')]
        ]
    )


async def change_operator(role, operator_tg_id, operator_username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔄 Заменить', callback_data=f'change_operator_{role}_{operator_tg_id}_{operator_username}')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_action')],
        ]
    )


async def start_answer(application_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✍ Написать ответ', callback_data=f'start_answer_{application_id}')]
        ]
    )


async def send_answer_now(application_id, answer_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📤 Отправить ответ', callback_data=f'answer_now_{application_id}_{answer_id}')]
        ]
)
