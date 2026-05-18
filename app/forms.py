from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class TaskForm(FlaskForm):
    title = StringField('Название задачи', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание', validators=[DataRequired()])
    category = SelectField('Категория', coerce=str)
    reward = IntegerField('Награда (₽)', validators=[DataRequired(), NumberRange(min=10)])
    cover_image = FileField('Обложка задачи', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg'])])
    file = FileField('Доп. файл', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'txt'])])
    is_premium = BooleanField('🔥 Сделать VIP')
    submit = SubmitField('Создать задачу')

class ProfileForm(FlaskForm):
    # Поле никнейма
    username = StringField('Никнейм', validators=[DataRequired(), Length(min=3, max=80)])
    # Поле "О себе" (about_me), чтобы совпадало с шаблоном
    about_me = TextAreaField('О себе (опыт, навыки)', validators=[Optional(), Length(max=500)])
    avatar = FileField('Аватар профиля', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg'])])
    submit = SubmitField('Сохранить изменения')