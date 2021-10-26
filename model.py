import datetime

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import *

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'df9d9b8a053375dbae2758d00192748b77c1208ddd6e478c65b35e982c3c633b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer(), primary_key=True)
    username = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False, default="teacher")
    last_login_time = Column(DateTime, default=datetime.datetime.now())
    usergroup = relationship('UserGroup',backref='user', lazy = 'dynamic')
    marks = relationship('Marks',backref='user', lazy = 'dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"user {self.username}"


class Course(db.Model):
    __tablename__ = "course"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    test = relationship('Test', backref='course', lazy='dynamic')
    lecture = relationship('Lecture', backref='course', lazy='dynamic')
    groupcourse = relationship('GroupCourse', backref='course', lazy='dynamic')


class GroupCourse(db.Model):
    __tablename__ = "groupcourse"
    id = Column(Integer(), primary_key = True)
    group_id = Column(Integer,ForeignKey('group.id'))
    course_id = Column(Integer,ForeignKey('course.id'))

class UserGroup(db.Model):
    __tablename__ = "usergroup"
    id = Column(Integer(), primary_key = True)
    group_id = Column(Integer,ForeignKey('group.id'))
    user_id = Column(Integer,ForeignKey('user.id'))

class Marks(db.Model):
    __tablename__ = "marks"
    id = Column(Integer(), primary_key = True)
    mark = Column(String(255), nullable = False)
    date = Column(DateTime, nullable = False)
    user_id = Column(Integer,ForeignKey('user.id'))
    part_id = Column(Integer, ForeignKey('part.id'))

class Test(db.Model):
    __tablename__ = "test"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    close_date = Column(DateTime, nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    part = relationship('Part', backref='test', lazy='dynamic')
    

class Part(db.Model):
    __tablename__ = "part"
    id = Column(Integer(), primary_key=True)
    text = Column(String(255),nullable = False)
    number = Column(Integer, nullable = False)
    test_id = Column(Integer, ForeignKey('test.id'))
    question = relationship('Question', backref='part', lazy='dynamic')
    marks = relationship('Marks',backref='part', lazy = 'dynamic')


class Question(db.Model):
    __tablename__ = "question"
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    number = Column(Integer, nullable = False)
    part_id = Column(Integer, ForeignKey('part.id'))
    answer = relationship('Answer', backref='question', lazy='dynamic')


class Answer(db.Model):
    __tablename__ = "answer"
    id = Column(Integer(), primary_key=True)
    text = Column(Text, nullable=False)
    isTrue = Column(Integer,nullable=False,default=0)
    question_id = Column(Integer, ForeignKey('question.id'))


class Group(db.Model):
    __tablename__ = "group"
    id = Column(Integer(), primary_key=True)
    name = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    notification = relationship('Notification', backref = 'group', lazy='dynamic')
    groupcourse = relationship('GroupCourse', backref='group', lazy='dynamic')
    usergroup = relationship('UserGroup',backref='group', lazy = 'dynamic')


class Notification(db.Model,SerializerMixin):
    __tablename__ = "notifications"
    serialize_only = ('id', 'text', 'date')
    id = Column(Integer(), primary_key = True)
    text = Column(String(255),nullable = False)
    date = Column(DateTime, nullable = false)
    group_id = Column(Integer, ForeignKey('group.id'))


class InviteCode(db.Model):
    __tablename__ = "invite_code"
    id = Column(Integer(), primary_key=True)
    text = Column(Text, nullable=False)


class Lecture(db.Model,SerializerMixin):
    __tablename__ = "lecture"
    serialize_only = ('id', 'title', 'sub_title', 'path_to_file')
    id = Column(Integer(), primary_key=True)
    title = Column(String(255), nullable=False)
    sub_title = Column(String(255),nullable=False)
    path_to_file = Column(String(255), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'))
    