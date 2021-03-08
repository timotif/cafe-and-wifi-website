import os
from functools import wraps
from flask import Flask, render_template, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_required, logout_user, current_user, login_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy.orm import relationship
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, SubmitField, BooleanField, PasswordField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, URL, Email

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '123')
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize migration to add column
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

login_manager = LoginManager()
login_manager.init_app(app)

# Global variables
headers = ['Cafe Name', 'Location', 'Seats', 'Toilet', 'Wifi', 'Calls', 'Power', 'Coffee']


# Initialize db
# class User(db.Model, UserMixin):  # Don't forget subclass UserMixin
#     __tablename__ = 'user'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True, nullable=False)
#     password = db.Column(db.String(250), nullable=False)
#     email = db.Column(db.String(80), unique=True, nullable=False)
#
#
# class Cafe(db.Model):
#     __tablename__ = 'cafe'
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(250), unique=True, nullable=False)
#     map_url = db.Column(db.String(500), nullable=False)
#     img_url = db.Column(db.String(500), nullable=False)
#     location = db.Column(db.String(250), nullable=False)
#     seats = db.Column(db.String(250), nullable=False)
#     has_toilet = db.Column(db.Boolean, nullable=False)
#     has_wifi = db.Column(db.Boolean, nullable=False)
#     has_sockets = db.Column(db.Boolean, nullable=False)
#     can_take_calls = db.Column(db.Boolean, nullable=False)
#     coffee_price = db.Column(db.String(250), nullable=True)
#
#     def to_dict(self):
#         return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# DB Initialize with User/Cafe relationship
class User(db.Model, UserMixin):  # Don't forget subclass UserMixin
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    cafes = relationship("Cafe", back_populates="user")


class Cafe(db.Model):
    __tablename__ = 'cafe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = relationship("User", back_populates="cafes")

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# db.create_all()

# To add a column use the migrate function:
# from flask_script import Manager
# from flask_migrate import Migrate, MigrateCommand
# migrate = Migrate(app, db)
# manager = Manager(app)
# manager.add_command('db', MigrateCommand)
# in the terminal "export FLASK_APP=main.py"
# "flask db init"
# It creates a directory "migrations"
# "flask db migrate -m "Initial migration.""
# "flask upgrade


# Create form
class CafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    img_url = StringField('Link to a pic')
    location = StringField('Location', validators=[DataRequired()])
    map_url = StringField('Location URL', validators=[DataRequired(), URL()])
    coffee_price = StringField('Coffee price', validators=[DataRequired()])
    has_toilet = BooleanField('Toilet for customers')
    has_wifi = BooleanField('Wifi')
    can_take_calls = BooleanField('Can take calls')
    has_sockets = BooleanField('Has sockets')
    seats = StringField('How many seats')
    submit = SubmitField('Submit')



class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class SearchCafe(FlaskForm):
    name = StringField('Name')
    location = StringField('Location')
    submit = SubmitField('Search')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def admin_only(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not current_user.id == 1:
            return abort(403)
        else:
            return function(*args, **kwargs)
    return decorated_function


@app.route("/")
def home():
    return render_template('index.html')


@app.route('/cafes')
def cafes():
    all_cafes = db.session.query(Cafe).all()
    list_of_rows = [cafe.to_dict() for cafe in all_cafes]
    contributors_dict = {cafe.user_id:retrieve_name(cafe.user_id) for cafe in all_cafes if cafe.user_id}
    return render_template('cafes.html', cafes=list_of_rows, headers=headers, contributors=contributors_dict)


@app.route('/retrieve')
def retrieve_name(user_id):
    user = User.query.get(user_id)
    return user.name


@app.route('/search', methods=['GET', 'POST'])
def search():
    # TODO Implement the search also for partial match on whatever column
    # TODO Flash the active filters in the result page
    search_form = SearchCafe()
    if search_form.validate_on_submit():
        search = []
        text = search_form.data['name']
        for cafe in Cafe.query.filter_by(name=text).all():
            print(cafe)
            search.append(cafe)
        search_result = [cafe.to_dict() for cafe in search]
        return render_template('cafes.html', cafes=search_result, headers=headers)
    return render_template('search.html', form=search_form)


@app.route('/add', methods=['GET', 'POST'])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login to add Cafes")
            return redirect(url_for('login'))
        else:
            new_cafe = Cafe(user_id = current_user.id)
            # I used to loop through request.form.get(att) but it wouldn't return the att for the unchecked booleans
            # I should loop through form.data instead
            for field in form.data:
                print(field)
                print(form.data.get(field))
                if field.startswith('has') or field.startswith('can'):
                    setattr(new_cafe, field, bool(form.data.get(field)))
                else:
                    setattr(new_cafe, field, form.data.get(field))
            db.session.add(new_cafe)
            db.session.commit()
            return redirect(url_for('cafes'))
    return render_template('add.html', form=form)


@app.route('/delete/<int:cafe_id>')
@admin_only
def delete_cafe(cafe_id):
    cafe_to_delete = Cafe.query.get(cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('cafes'))


@app.route('/register', methods=['GET', 'POST'])
def register_user():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        new_user = User()
        data = register_form.data
        if User.query.filter_by(email=data['email']).first():
            flash('Already registered. Login instead')
            return redirect(url_for('login'))
        else:
            for field in data:
                if field != 'password':
                    setattr(new_user, field, data[field])
                else:
                    new_user.password = generate_password_hash(register_form.password.data, method='pbkdf2:sha256',
                                                               salt_length=8)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('home'))
    return render_template('register.html', form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        # User not in db
        if not user:
            flash('User not recognized')
            return redirect(url_for('login'))
        # Wrong password
        elif not check_password_hash(user.password, login_form.password.data):
            flash("The password is wrong")
            return redirect(url_for('login'))
        # Login info confirmed
        else:
            flash("Login successful")
            login_user(user)
            return redirect(url_for("cafes"))
    return render_template('login.html', form=login_form)


@app.route('/secret')
@login_required
def secret_page():
    return "<h1>Secret</h1>"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8080")
    # manager.run()