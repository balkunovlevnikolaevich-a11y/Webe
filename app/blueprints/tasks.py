import os
import PyPDF2
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from .. import db
from ..models import Task, TaskStatus, User, Message, Category, SiteSetting, Review, Ticket
from ..forms import TaskForm

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('/list')
def list_tasks():
    category_name = request.args.get('category')
    query = Task.query
    if category_name:
        query = query.filter(Task.category == category_name)
    tasks = query.order_by(Task.is_premium.desc(), Task.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('list_tasks.html', tasks=tasks, categories=categories, current_category=category_name)

@tasks_bp.route('/my')
@login_required
def my_tasks():
    created = Task.query.filter_by(customer_id=current_user.id).all()
    taken = Task.query.filter_by(executor_id=current_user.id).all()
    return render_template('my_tasks.html', created_at_tasks=created, taken_tasks=taken)

@tasks_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.username.lower() != 'admin':
        flash('Доступ запрещен!', 'error')
        return redirect(url_for('tasks.list_tasks'))

    # Обработка формы: Сохранение цен
    if request.method == 'POST':
        # Сохраняем цену OCR
        new_ocr_price = request.form.get('ocr_price')
        if new_ocr_price and new_ocr_price.isdigit():
            setting_ocr = SiteSetting.query.filter_by(key='ocr_price').first()
            if not setting_ocr:
                setting_ocr = SiteSetting(key='ocr_price', value=new_ocr_price)
                db.session.add(setting_ocr)
            else:
                setting_ocr.value = new_ocr_price
                
        # Сохраняем цену Премиум (ТОП)
        new_premium_price = request.form.get('premium_price')
        if new_premium_price and new_premium_price.isdigit():
            setting_prem = SiteSetting.query.filter_by(key='premium_price').first()
            if not setting_prem:
                setting_prem = SiteSetting(key='premium_price', value=new_premium_price)
                db.session.add(setting_prem)
            else:
                setting_prem.value = new_premium_price

        db.session.commit()
        flash('Ценовая политика успешно обновлена!', 'success')
        return redirect(url_for('tasks.admin_panel'))
    
    # Сбор статистики
    users = User.query.all()
    all_tasks = Task.query.all()
    active_tasks_count = Task.query.filter_by(status=TaskStatus.TAKEN).count()
    confirmed_tasks = Task.query.filter_by(status=TaskStatus.CONFIRMED).all()
    total_turnover = sum(task.reward for task in confirmed_tasks)
    
    # Загружаем текущие цены из БД
    setting_ocr = SiteSetting.query.filter_by(key='ocr_price').first()
    current_ocr_price = int(setting_ocr.value) if setting_ocr else 10
    
    setting_prem = SiteSetting.query.filter_by(key='premium_price').first()
    current_premium_price = int(setting_prem.value) if setting_prem else 100
    
    # Загружаем только Открытые тикеты
    tickets = Ticket.query.filter_by(status='Открыт').order_by(Ticket.created_at.desc()).all()
    
    return render_template('admin.html', 
                           users=users,
                           users_count=len(users), 
                           active_tasks_count=active_tasks_count, 
                           total_turnover=total_turnover,
                           tasks=all_tasks,
                           current_ocr_price=current_ocr_price,
                           current_premium_price=current_premium_price,
                           tickets=tickets)

@tasks_bp.route('/admin/task/<int:task_id>/cancel')
@login_required
def admin_cancel_task(task_id):
    if current_user.username.lower() != 'admin':
        return redirect(url_for('main.index'))
    task = Task.query.get_or_404(task_id)
    task.status = TaskStatus.ARCHIVED
    db.session.commit()
    flash('Задача отменена администратором!', 'success')
    return redirect(url_for('tasks.admin_panel'))

@tasks_bp.route('/admin/ticket/<int:ticket_id>/close')
@login_required
def admin_close_ticket(ticket_id):
    if current_user.username.lower() != 'admin':
        return redirect(url_for('main.index'))
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = 'Закрыт'
    db.session.commit()
    flash('Тикет закрыт. Вопрос решен.', 'success')
    return redirect(url_for('tasks.admin_panel'))

@tasks_bp.route('/<int:task_id>')
def task_detail(task_id):
    task = Task.query.get_or_404(task_id)
    messages = Message.query.filter_by(task_id=task_id).all()
    
    setting = SiteSetting.query.filter_by(key='ocr_price').first()
    ocr_price = int(setting.value) if setting else 10
    
    return render_template('task_detail.html', task=task, messages=messages, ocr_price=ocr_price)

@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TaskForm()
    form.category.choices = [(c.name, c.name) for c in Category.query.all()]
    
    # 🔥 Достаем цену ТОПа безопасно (с защитой от пустых значений) 🔥
    setting_prem = SiteSetting.query.filter_by(key='premium_price').first()
    try:
        premium_price = int(setting_prem.value) if setting_prem and setting_prem.value else 100 
    except (ValueError, TypeError):
        premium_price = 100
    
    if form.validate_on_submit():
        
        # 🔥 ПРОВЕРКА БАЛАНСА И СПИСАНИЕ ЗА ТОП 🔥
        if form.is_premium.data:
            if current_user.balance < premium_price:
                flash(f'Недостаточно средств для ТОП-размещения. Нужно {premium_price} ₽ на балансе.', 'error')
                # 🔥 ИСПРАВЛЕНИЕ: Обязательно передаем premium_price при ошибке и перезагрузке формы! 🔥
                return render_template('create_task.html', form=form, premium_price=premium_price)
            
            current_user.balance -= premium_price

        task = Task(
            title=form.title.data,
            description=form.description.data,
            reward=form.reward.data,
            category=form.category.data,
            customer_id=current_user.id,
            is_premium=form.is_premium.data
        )
        if form.cover_image.data:
            f = form.cover_image.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            task.cover_image = filename
        if form.file.data:
            f = form.file.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            task.file_name = filename
            
        db.session.add(task)
        db.session.commit()
        
        if task.is_premium:
            flash('Задача успешно создана и закреплена в ТОПе!', 'success')
        else:
            flash('Задача создана!', 'success')
            
        return redirect(url_for('tasks.list_tasks'))
    
    # 🔥 Передаем premium_price при первой загрузке страницы 🔥
    return render_template('create_task.html', form=form, premium_price=premium_price)

@tasks_bp.route('/<int:task_id>/send_message', methods=['POST'])
@login_required
def send_message(task_id):
    text = request.form.get('text')
    file = request.files.get('chat_file')
    
    msg = Message(task_id=task_id, sender_id=current_user.id, text=text)
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        msg.file_name = filename
        
    db.session.add(msg)
    db.session.commit()
    return redirect(url_for('tasks.task_detail', task_id=task_id))

@tasks_bp.route('/<int:task_id>/take')
@login_required
def take_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.status == TaskStatus.OPEN and task.customer_id != current_user.id:
        task.executor_id = current_user.id
        task.status = TaskStatus.TAKEN
        db.session.commit()
        flash('Вы взяли задачу в работу!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task.id))

@tasks_bp.route('/<int:task_id>/complete')
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.executor_id == current_user.id and task.status == TaskStatus.TAKEN:
        task.status = TaskStatus.COMPLETED
        db.session.commit()
        flash('Задача отмечена как выполненная!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task.id))

@tasks_bp.route('/<int:task_id>/confirm')
@login_required
def confirm_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.customer_id == current_user.id and task.status == TaskStatus.COMPLETED:
        task.status = TaskStatus.CONFIRMED
        task.executor.balance += task.reward
        db.session.commit()
        flash('Выполнение подтверждено, оплата отправлена исполнителю!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task.id))

@tasks_bp.route('/<int:task_id>/review', methods=['POST'])
@login_required
def leave_review(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.id == task.customer_id and not task.has_review:
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment')
        review = Review(task_id=task.id, author_id=current_user.id, recipient_id=task.executor_id, rating=rating, comment=comment)
        task.has_review = True
        db.session.add(review)
        db.session.commit()
        flash('Отзыв оставлен!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task.id))

@tasks_bp.route('/<int:task_id>/ocr', methods=['POST'])
@login_required
def order_ocr(task_id):
    task = Task.query.get_or_404(task_id)
    setting = SiteSetting.query.filter_by(key='ocr_price').first()
    ocr_price = int(setting.value) if setting else 10

    if current_user.balance < ocr_price:
        flash(f'Недостаточно средств. Нужно {ocr_price} ₽.', 'error')
        return redirect(url_for('tasks.task_detail', task_id=task_id))

    if not task.file_name:
        flash('К задаче не прикреплен файл ТЗ!', 'error')
        return redirect(url_for('tasks.task_detail', task_id=task_id))

    current_user.balance -= ocr_price
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], task.file_name)
    extracted_text = "Не удалось распознать текст. Возможно, документ пуст."
    
    try:
        if task.file_name.lower().endswith('.pdf'):
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
                if text.strip(): extracted_text = text.strip()
                else: extracted_text = "PDF состоит из картинок. Текст не найден."
        elif task.file_name.lower().endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
        else:
            extracted_text = "Автоматическая расшифровка пока поддерживает только форматы PDF и TXT."
    except Exception as e:
        extracted_text = f"Произошла ошибка при чтении файла: {str(e)}"

    message_text = f"🤖 Система Prochekt_Web: Расшифровка файла «{task.file_name}» завершена!\n\nТекст документа:\n{extracted_text}"
    msg = Message(task_id=task.id, sender_id=current_user.id, text=message_text)
    
    db.session.add(msg)
    db.session.commit()
    flash('Файл ТЗ успешно расшифрован!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task_id))

@tasks_bp.route('/<int:task_id>/support')
@login_required
def support(task_id):
    ticket = Ticket(user_id=current_user.id, task_id=task_id)
    db.session.add(ticket)
    db.session.commit()
    flash('Ваш запрос зафиксирован. Админ уже видит его в панели!', 'success')
    return redirect(url_for('tasks.task_detail', task_id=task_id))

@tasks_bp.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
