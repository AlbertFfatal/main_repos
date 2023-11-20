from flask_sqlalchemy import SQLAlchemy
from cloudipsp import Api, Checkout
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///proj.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '18062023'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(127), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=False)

    # text = db.Column(db.Text)
    def __repr__(self):
        return self.title


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            # пользователь уже существует
            flash('Username already exists')
            return render_template('register.html', message="Пользователь уже существует")

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('home'))  # Redirect to home page after successful registration

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))  # Redirect to home page after successful login

        flash('Invalid username or password')
        return render_template('login.html', message="Неправильное имя пользователя или пароль")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    items = Item.query.order_by(Item.price).all()
    return render_template('index.html', data=items)


@app.route('/buy/<int:id>')
@login_required
def buy(id):
    item = Item.query.get(id)

    api = Api(merchant_id=1396424,
              secret_key='test')
    checkout = Checkout(api=api)
    data = {
        "currency": "RUB",
        "amount": str(item.price) + "00"
    }
    url = checkout.url(data).get('checkout_url')
    return redirect(url)


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    if request.method == "POST":
        title = request.form['title']
        price = request.form['price']
        item = Item(title=title, price=price)
        try:
            db.session.add(item)
            db.session.commit()
            return redirect('/home')
        except:
            return "Ошибка"
    else:
        return render_template('create.html')


if __name__ == "__main__":
    with app.app_context():  # Создаем контекст приложения
        db.create_all()  # Создаем все таблицы
    app.run(debug=True)
