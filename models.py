# models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuthInfo(Base):
    __tablename__ = "auth_info"
    id_auth = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=True)
    password = Column(String, nullable=True)


class Conference(Base):
    __tablename__ = "conference"
    id = Column(Integer, primary_key=True, autoincrement=True)
    link = Column(String, nullable=True)


class Gender(Base):
    __tablename__ = "gender"
    id_gender = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)


class Nationality(Base):
    __tablename__ = "nationality"
    id_nation = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)


class PersonalInfo(Base):
    __tablename__ = "personal_info"
    id_personal = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=True)
    second_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)


class Person(Base):
    __tablename__ = "person"
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Текстові поля замість ID довідників
    organization_name = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    
    # Зв'язки, що залишилися
    id_nation = Column(Integer, ForeignKey("nationality.id_nation"))
    id_gender = Column(Integer, ForeignKey("gender.id_gender"))
    id_auth = Column(Integer, ForeignKey("auth_info.id_auth"))
    id_personal = Column(Integer, ForeignKey("personal_info.id_personal"))


class UsersConference(Base):
    __tablename__ = "users_conference"
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_person = Column(Integer, ForeignKey("person.id"))
    id_conf = Column(Integer, ForeignKey("conference.id"))