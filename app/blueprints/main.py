from flask import Blueprint, render_template, redirect, url_for, request, current_app, flash
from flask_login import login_required, current_user
from sqlalchemy import func
import os
import base64
from .. import db
from ..models import User, Review, Task
from ..forms import ProfileForm
from ..models import User, Review, Task


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    db.session.refresh(current_user)
    return render_template('dashboard.html')

@main_bp.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    
    # Расчет средней оценки исполнителя
    reviews = Review.query.filter_by(recipient_id=user.id).all()
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        
    return render_template('profile.html', user=user, avg_rating=avg_rating, reviews=reviews)

@main_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    if form.validate_on_submit():
        # Обработка аватарки из Cropper.js
        cropped_data = request.form.get('cropped_avatar')
        if cropped_data and "," in cropped_data:
            header, encoded = cropped_data.split(",", 1)
            image_data = base64.b64decode(encoded)
            filename = f"avatar_{current_user.id}.jpg"
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            with open(os.path.join(upload_path, filename), "wb") as f:
                f.write(image_data)
            current_user.avatar = filename

        current_user.username = form.username.data
        current_user.bio = form.about_me.data 
        db.session.commit()
        flash('Профиль обновлен!', 'success')
        return redirect(url_for('main.profile', username=current_user.username))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.bio 
        
    return render_template('edit_profile.html', form=form)