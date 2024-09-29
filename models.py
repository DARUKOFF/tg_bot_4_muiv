from sqlalchemy import BigInteger, ForeignKey, String, Integer, Column, Boolean, DateTime, Enum, Index
from typing import List
from sqlalchemy.orm import relationship, declarative_base, Mapped
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


from settings import SQLALCHEMY_URL


engine = create_async_engine(SQLALCHEMY_URL, echo=True)
async_session = async_sessionmaker(engine)


Base = declarative_base()

    
class Students(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=True, unique=True)
    full_name = Column(String(100), nullable=False)
    student_id = Column(String(50), nullable=False, unique=True)
    group_id = Column(String(50), nullable=False)
    phone_number = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=True)
    is_eligible = Column(Boolean, default=True)

    application_rel = relationship("Applications", back_populates="students_rel")

    __table_args__ = (
        Index('ix__st_tg_id', 'tg_id'),
    )


class Operators(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(String(100), nullable=False)
    role = Column(Enum('documents', 'terms', 'finances', name='role'), nullable=False)
    is_eligible = Column(Boolean, default=True)

    application_rel = relationship("Applications", back_populates="operators_rel")

    __table_args__ = (
        Index('ix_op_tg_id', 'tg_id'),
    )


class Applications(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(Enum('documents', 'terms', 'finances', name='category'), nullable=False)
    text = Column(String, nullable=False)
    start_date = Column(DateTime, nullable=False)
    finish_date = Column(DateTime)
    status = Column(Enum('applied', 'process', 'completed', name='application_status'), nullable=False, default='applied')
    
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    operator_id = Column(Integer, ForeignKey('operators.id'), nullable=False)
    answer_id = Column(Integer, ForeignKey('answers.id'), nullable=True)

    files_rel: Mapped[List['ApplicationFiles']] = relationship(back_populates="application_rel")
    students_rel = relationship("Students", back_populates="application_rel")
    operators_rel = relationship("Operators", back_populates="application_rel")

    __table_args__ = (
        Index('ix_student_id', 'student_id'),
        Index('ix_operator_id', 'operator_id'),
    )


class ApplicationFiles(Base):
    __tablename__ = "application_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_type = Column(Enum('document', 'photo', 'audio', 'video', name='file_type'), nullable=False)
    file_id = Column(String, nullable=False)

    application_id = Column(Integer, ForeignKey('applications.id'), nullable=True)

    application_rel = relationship("Applications", back_populates="files_rel")

    __table_args__ = (
        Index('ix_file_id', 'file_id'),
    )


class Answers(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String, nullable=False)

    application_id = Column(Integer, ForeignKey('applications.id'), nullable=False)

    answer_files_rel: Mapped[List['AnswerFiles']] = relationship(back_populates="answer_rel")

    __table_args__ = (
        Index('ix_application_id', 'application_id'),
    )


class AnswerFiles(Base):
    __tablename__ = "answer_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    answer_file_type = Column(Enum('document', 'photo', 'audio', 'video', name='answer_file_type'), nullable=False)
    answer_file_id = Column(String, nullable=False)

    answer_id = Column(Integer, ForeignKey('answers.id'), nullable=True)

    answer_rel = relationship("Answers", back_populates="answer_files_rel")

    __table_args__ = (
        Index('ix_answer_id', 'answer_id'),
    )


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        