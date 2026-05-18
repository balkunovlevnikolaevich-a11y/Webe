from app import create_app, db
from app.models import User, Task, Category, TaskStatus

app = create_app()

# ВЫНОСИМ ЭТО ИЗ-ПОД IF, чтобы Gunicorn это увидел
with app.app_context():
    # Создаем таблицы (если их еще нет)
    db.create_all()
    
    # Наполняем категориями
    if not Category.query.first():
        categories = ['Веб-разработка', 'Дизайн', 'Тексты', 'Маркетинг', 'Прочее']
        for cat_name in categories:
            db.session.add(Category(name=cat_name))
        db.session.commit()
        print("✅ База данных и категории инициализированы!")

# Этот блок теперь нужен только для локальной разработки
if __name__ == '__main__':
    app.run(debug=True)
