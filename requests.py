from data.models import async_session, Applications, Operators, Students, ApplicationFiles, Answers, AnswerFiles
from sqlalchemy import select, update, func
from datetime import datetime
import random


async def save_from_xlsx(full_name, group_id, student_id, phone_number):
    async with async_session() as session:
        student = await session.scalar(select(Students).where(Students.student_id == student_id))
        if not student:
            new_student = Students(full_name=full_name, group_id=group_id, 
                                student_id=student_id, phone_number=phone_number)
            session.add(new_student)
            await session.commit()


async def get_students():
    async with async_session() as session:
        students = await session.scalars(select(Students))
        return students
    

async def get_students_tg_ids():
    async with async_session() as session:
        result = []
        students = await session.scalars(select(Students))
        for student in students:
            result.append(student.tg_id)
        return result
    

async def edit_student(student_id, action):
    async with async_session() as session:
        await session.execute(update(Students).where(Students.id == student_id).values(
            is_eligible=False if action == 'restrict' else True))
        await session.commit()


async def set_student(student_id, tg_id):
    async with async_session() as session:
        student = await session.scalar(select(Students).where(Students.student_id == student_id))
        now = datetime.now()
        if student:
            student.tg_id = tg_id
            student.date = now
            await session.commit()
            return True
        else:
            return False
        

async def get_student_by_id(stud_id):
    async with async_session() as session:
        student = await session.scalar(select(Students).where(Students.id == stud_id))
        return student
        

async def get_eligible_student_by_tg(tg_id):
    async with async_session() as session:
        student = await session.scalar(select(Students).where(Students.tg_id == tg_id))
        if student and student.is_eligible:
            return student
        else:
            return False
        

async def get_operator_by_role(role):
    async with async_session() as session:
        operator = await session.scalar(select(Operators).where(Operators.role == role))
        return operator


async def get_operators_tg_ids():
    async with async_session() as session:
        result = []
        operators = await session.scalars(select(Operators))
        for operator in operators:
            result.append(operator.tg_id)
        return result


async def check_operators_presence():
    async with async_session() as session:
        operators = await session.scalars(select(Operators))
        print(operators)
        for operator in operators:
            if operator and operator.is_eligible:
                return True
        return False


async def get_operator_by_id(operator_id):
    async with async_session() as session:
        operator = await session.scalar(select(Operators).where(Operators.id == operator_id))
        return operator

async def get_operator_for_send(operator_id=None):
    async with async_session() as session:
        if operator_id:
            operator = await session.scalar(select(Operators).where(Operators.id == operator_id))
            if operator and operator.is_eligible:
                return operator
        else:
            free_operator = await get_free_operator()
            if free_operator:
                return free_operator
            else:
                # Если нет операторов с активными задачами - возвращаем id случайного оператора
                return await get_random_operator(operator_id)


async def get_free_operator():
    async with async_session() as session:
        # Подсчет количества активных заявок для каждого оператора
        subquery = (
            select(
                Applications.operator_id,
                func.count(Applications.id).label('active_count')
            )
            .where(Applications.status != 'completed')  # Условие для активных задач
            .group_by(Applications.operator_id)
            .subquery()
        )
        # Выбор оператора с наименьшим количеством активных задач, который также имеет права
        operator = await session.scalar(
            select(Operators)
            .outerjoin(subquery, Operators.id == subquery.c.operator_id)
            .where(Operators.is_eligible == True)  # Проверка наличия прав
            .order_by(subquery.c.active_count)  # Сортируем по активным задачам
            .limit(1)
        )
        return operator


async def get_random_operator(operator_id):
    async with async_session() as session:
        eligible_operators = await session.scalars(
            select(Operators).where(Operators.id != operator_id, Operators.is_eligible == True)
        )
        eligible_ids = [op.id for op in eligible_operators]
        random_operator_id = random.choice(eligible_ids)
        return await session.scalar(select(Operators).where(Operators.id == random_operator_id))


async def check_role(role):
    async with async_session() as session:
        operator = await session.scalar(select(Operators).where(Operators.role == role))
        return operator


async def set_operator(role, tg_id, username):
    async with async_session() as session:
        new_operator = Operators(role=role, tg_id=tg_id, username=username)
        session.add(new_operator)
        await session.commit()
        

async def get_eligible_operators():
    async with async_session() as session:
        operators = await session.scalars(select(Operators).where(Operators.is_eligible==True))
        return operators


async def get_uneligible_operators():
    async with async_session() as session:
        operators = await session.scalars(select(Operators).where(Operators.is_eligible==False))
        return operators
    

async def change_operator(role, operator_tg_id, operator_username):
    async with async_session() as session:
        await session.execute(update(Operators).where(Operators.role == role).values(
            tg_id=operator_tg_id, username=operator_username, is_eligible=True
        ))
        await session.commit()


async def edit_operator(operator_id, action, role=None):
    async with async_session() as session:
        if action in ('restrict', 'restore'):
            await session.execute(update(Operators).where(
                Operators.id == operator_id).values(is_eligible=False if action=='restrict' else True))
        elif role:
            await session.execute(update(Operators).where(Operators.role == role).values(is_eligible=True))
            await session.execute(update(Operators).where(
                Operators.id == operator_id).values(role=role))
        await session.commit()


async def set_application(data):
    async with async_session() as session:
        new_application = Applications(**data)
        session.add(new_application)
        await session.commit()
        await session.refresh(new_application)
        return new_application.id
    

async def get_application_by_id(application_id):
    async with async_session() as session:
        application = await session.scalar(select(Applications).where(Applications.id == application_id))
        return application
    

async def save_file(file_type, file_id, application_id):
    async with async_session() as session:
        new_file = ApplicationFiles(file_type=file_type, file_id=file_id, application_id=application_id)
        session.add(new_file)
        await session.commit()
    

async def get_files_by_application_id(application_id):
    async with async_session() as session:
        result = await session.execute(select(ApplicationFiles).where(ApplicationFiles.application_id == application_id))
        files = result.scalars().all()
        return files
   

async def change_application_status(application_id, status=None, answer_id=None):
    async with async_session() as session:
        now_str = datetime.now().strftime(f"%Y.%m.%d %H:%M:%S")
        now = datetime.strptime(now_str, f"%Y.%m.%d %H:%M:%S")
        update_values = {}
        if status:
            update_values['status'] = status
        if answer_id:
            update_values['status'] = 'completed'
            update_values['answer_id'] = answer_id
            update_values['finish_date'] = now
        if update_values:
            await session.execute(
                update(Applications)
                .where(Applications.id == application_id)
                .values(**update_values)
            )
        await session.commit()


async def get_applications_by_student(student_id):
    async with async_session() as session:
        applications = await session.scalars(select(Applications).where(
            Applications.student_id == student_id))
        return applications
    

async def get_applications_by_status_and_operator(status, operator_tg_id):
    async with async_session() as session:
        operator = await session.scalar(select(Operators).where(Operators.tg_id == operator_tg_id))
        applications = await session.scalars(select(Applications).where(
            Applications.operator_id == operator.id, Applications.status == status))
        return applications


async def save_answer(text, application_id):
    async with async_session() as session:
        new_answer = Answers(text=text, application_id=application_id)
        session.add(new_answer)
        await session.commit()
        await session.refresh(new_answer)
        return new_answer.id

async def save_answer_file(file_type, file_id, answer_id):
    async with async_session() as session:
        new_file = AnswerFiles(answer_file_type=file_type,  answer_file_id=file_id, answer_id=answer_id)
        session.add(new_file)
        await session.commit()
    
async def get_files_by_answer_id(answer_id):
    async with async_session() as session:
        result = await session.execute(select(AnswerFiles).where(AnswerFiles.answer_id == answer_id))
        files = result.scalars().all()
        return files

async def get_answer_by_id(answer_id):
    async with async_session() as session:
        answer = await session.scalar(select(Answers).where(Answers.id == answer_id))
        return answer