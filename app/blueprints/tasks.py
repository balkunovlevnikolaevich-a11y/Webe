@tasks_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = TaskForm()
    form.category.choices = [(c.name, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        
        # 🔥 БЛОК ПРОВЕРКИ И СПИСАНИЯ ДЕНЕГ ЗА ТОП 🔥
        if form.is_premium.data:
            # Ищем цену премиума в настройках сайта
            setting_prem = SiteSetting.query.filter_by(key='premium_price').first()
            premium_price = int(setting_prem.value) if setting_prem else 100 # 100 руб по умолчанию
            
            # Проверяем, хватает ли у юзера денег
            if current_user.balance < premium_price:
                flash(f'Недостаточно средств для ТОП-размещения. Нужно {premium_price} ₽ на балансе.', 'error')
                return render_template('create_task.html', form=form) # Возвращаем обратно на форму
            
            # Если денег хватает - списываем с баланса
            current_user.balance -= premium_price

        # Создаем саму задачу
        task = Task(
            title=form.title.data,
            description=form.description.data,
            reward=form.reward.data,
            category=form.category.data,
            customer_id=current_user.id,
            is_premium=form.is_premium.data
        )
        
        # Сохраняем обложку, если есть
        if form.cover_image.data:
            f = form.cover_image.data
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            task.cover_image = filename
            
        # Сохраняем файл ТЗ, если есть
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
        
    return render_template('create_task.html', form=form)
