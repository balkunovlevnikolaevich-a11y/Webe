from app import create_app, db
from app.models import User, Task, Category, TaskStatus

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Создаем таблицы
        db.create_all()
        
        # Категории
        if not Category.query.first():
            categories = ['Веб-разработка', 'Дизайн', 'Тексты', 'Маркетинг', 'Прочее']
            for cat_name in categories:
                db.session.add(Category(name=cat_name))
            db.session.commit()
            print("✅ Категории созданы!")

    app.run(debug=True)