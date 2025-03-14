from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import session
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['UPLOAD_EXTENSIONS'] = {'.jpg', '.jpeg', '.png', '.gif'}
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'

# Mô hình User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    profile_pic = db.Column(db.String(200), default="default.png")

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

# Mô hình danh mục
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Mô hình công việc
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=db.backref('tasks', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    if User.query.filter_by(email=email).first():
        flash('Email đã tồn tại.', 'danger')
        return redirect(url_for('home'))
    
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('Đăng ký thành công!', 'success')
    return redirect(url_for('home'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    
    if user and bcrypt.check_password_hash(user.password, password):
        if user.is_blocked:
            flash('Tài khoản của bạn đã bị khóa.', 'danger')
            return redirect(url_for('home'))
        login_user(user)
        return redirect(url_for('dashboard'))
    
    flash('Thông tin đăng nhập không hợp lệ.', 'danger')
    return redirect(url_for('home'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Bạn đã đăng xuất!', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST']) 
@login_required
def dashboard():
    if request.method == 'POST':
        title = request.form.get('title')
        category_id = request.form.get('category_id')
        if title and category_id:
            new_task = Task(title=title, category_id=category_id)
            db.session.add(new_task)
            db.session.commit()
            flash('Công việc đã được thêm!', 'success')
        return redirect(url_for('dashboard'))  # Chuyển hướng về lại trang
    categories = Category.query.all()
    tasks = Task.query.all()
    return render_template("dashboard.html", user=current_user, categories=categories, tasks=tasks)



@app.route('/categories', methods=['POST'])
@login_required
def add_category():
    name = request.form.get('name')
    if name:
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        flash('Danh mục đã được thêm!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tasks', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    if title and category_id:
        new_task = Task(title=title, category_id=category_id)
        db.session.add(new_task)
        db.session.commit()
        flash('Công việc đã được thêm!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        flash('Không có file nào được tải lên!', 'danger')
        return redirect(url_for('dashboard'))
    
    file = request.files['avatar']
    if file.filename == '':
        flash('Vui lòng chọn file!', 'danger')
        return redirect(url_for('dashboard'))

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext in app.config['UPLOAD_EXTENSIONS']:
        filename = f'user_{current_user.id}{file_ext}'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        current_user.profile_pic = f'uploads/{filename}'
        db.session.commit()
        flash('Cập nhật ảnh đại diện thành công!', 'success')
    else:
        flash('Định dạng file không hợp lệ!', 'danger')

    return redirect(url_for('dashboard'))


@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task.status = "Hoàn thành"
        task.completed_at = datetime.utcnow()
        db.session.commit()
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@gmail.com', password=bcrypt.generate_password_hash('admin123').decode('utf-8'), is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)