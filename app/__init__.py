from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Базовая конфигурация
    app.config['SECRET_KEY'] = 'dev-key-123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
    login_manager.login_message_category = "info"

    # Регистрация блюпринтов с правильными префиксами
    from .blueprints.auth import auth_bp
    from .blueprints.main import main_bp
    from .blueprints.tasks import tasks_bp

    # Добавляем url_prefix, чтобы пути /auth/login и /tasks/list заработали
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp) # Для главной страницы префикс обычно не нужен
    app.register_blueprint(tasks_bp, url_prefix='/tasks')

    # Импорт моделей (реклама удалена полностью)
    from .models import User 

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app