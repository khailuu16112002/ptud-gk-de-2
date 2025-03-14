from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from flask import Flask, request, jsonify
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


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    status = db.Column(db.String(50))
    created = db.Column(db.DateTime)
    finished = db.Column(db.DateTime, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref='tasks')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))



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

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).all()  # Lấy task của user hiện tại
    categories = Category.query.all()  # Lấy danh sách category (nếu có)
    return render_template('dashboard.html', tasks=tasks, categories=categories, user=current_user)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            new_category = Category(name=name)
            db.session.add(new_category)
            db.session.commit()
            flash('Thêm danh mục thành công!', 'success')
        return redirect(url_for('manage_categories'))

    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/delete_category/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Xóa danh mục thành công!', 'success')
    return redirect(url_for('manage_categories'))

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    name = request.form.get('name')
    status = request.form.get('status')
    created_at_str = request.form.get('created_at')
    completed_at_str = request.form.get('completed_at')
    category_id = request.form.get('category')  # Lấy category_id từ form

    created_at = datetime.strptime(created_at_str, '%Y-%m-%d')
    completed_at = datetime.strptime(completed_at_str, '%Y-%m-%dT%H:%M') if completed_at_str else None

    # Kiểm tra logic thời gian
    if completed_at and completed_at < created_at:
        flash("Thời gian hoàn thành không thể trước thời gian tạo!", "danger")
        return redirect(url_for('dashboard'))

    new_task = Task(title=name, status=status, created=created_at, finished=completed_at, user_id=current_user.id, category_id=category_id)
    db.session.add(new_task)
    db.session.commit()

    flash("Công việc đã được thêm!", "success")
    return redirect(url_for('dashboard'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    task_id = request.json.get('task_id')
    task = Task.query.get(task_id)
    
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({"success": True, "message": "Công việc đã được xóa thành công!"})
    else:
        return jsonify({"success": False, "message": "Công việc không tồn tại!"}), 404



@app.route('/complete_task/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash("Bạn không có quyền cập nhật công việc này!", "danger")
        return redirect(url_for('dashboard'))
    
    # Lấy thời gian hoàn thành từ form
    finished_time_str = request.form.get('finished_time')  # Dữ liệu từ form
    if not finished_time_str:
        flash("Vui lòng nhập thời gian hoàn thành!", "danger")
        return redirect(url_for('dashboard'))
    
    try:
        finished_time = datetime.strptime(finished_time_str, '%Y-%m-%d %H:%M')  # Chuyển chuỗi thành datetime
    except ValueError:
        flash("Định dạng thời gian không hợp lệ!", "danger")
        return redirect(url_for('dashboard'))
    
    # Kiểm tra thời gian hoàn thành có hợp lệ không
    if finished_time < task.created:
        flash("Thời gian hoàn thành không thể trước thời gian tạo!", "danger")
        return redirect(url_for('dashboard'))
    
    # Cập nhật thông tin
    task.status = 1  # Đánh dấu là hoàn thành
    task.finished = finished_time
    db.session.commit()
    flash("Công việc đã hoàn thành!", "success")

    return redirect(url_for('dashboard'))




if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@gmail.com', password=bcrypt.generate_password_hash('admin123').decode('utf-8'), is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)