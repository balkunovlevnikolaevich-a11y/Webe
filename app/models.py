import enum
from datetime import datetime
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class TaskStatus(enum.Enum):
    OPEN = 'Открыта'
    TAKEN = 'Принята'
    COMPLETED = 'Выполнена'
    CONFIRMED = 'Подтверждена'
    ARCHIVED = 'Архив'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Integer, default=0)
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    reviews_received = db.relationship('Review', foreign_keys='Review.recipient_id', backref='recipient', lazy=True)
    reviews_authored = db.relationship('Review', foreign_keys='Review.author_id', backref='author', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reward = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(100))
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.OPEN)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    executor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cover_image = db.Column(db.String(200))
    file_name = db.Column(db.String(200))
    is_premium = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    has_review = db.Column(db.Boolean, default=False)

    customer = db.relationship('User', foreign_keys=[customer_id], backref='tasks_created')
    executor = db.relationship('User', foreign_keys=[executor_id], backref='tasks_taken')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text)
    file_name = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', backref='messages')

class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200))

# 🔥 НОВАЯ ТАБЛИЦА ДЛЯ ПОДДЕРЖКИ 🔥
class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    status = db.Column(db.String(50), default='Открыт')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='tickets')
    task = db.relationship('Task', backref='tickets')