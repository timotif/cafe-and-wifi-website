from flask import Flask, render_template, request, url_for, redirect
import os

from flask import Flask, render_template, request, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, URL

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '123')
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


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


@app.route("/")
def home():
    return render_template('index.html')


# TODO Send to cafes.html a list of dictionaries from the db
@app.route('/cafes')
def cafes():
    all_cafes = db.session.query(Cafe).all()
    list_of_rows = [cafe.to_dict() for cafe in all_cafes]
    headers = ['Cafe Name', 'Location', 'Seats', 'Toilet', 'Wifi', 'Calls', 'Power', 'Coffee']
    return render_template('cafes.html', cafes=list_of_rows, headers=headers)


@app.route('/add', methods=['GET', 'POST'])
def add_cafe():
    form = CafeForm()
    if form.validate_on_submit():
        # print('Sending form')
        # print('VALIDATED')
        # In order to get values also for the unchecked boolean fields I loop through form for getting the id attribute
        # rather than request.form.get(att) that wouldn't return the att for the unchecked booleans
        new_cafe = Cafe()
        for field in form:
            # print(field.id)
            # print(request.form.get(field.id))
            if field.id.startswith('has') or field.id.startswith('can'):
                setattr(new_cafe, field.id, bool(request.form.get(field.id)))
            else:
                setattr(new_cafe, field.id, request.form.get(field.id))
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('cafes'))
    return render_template('add.html', form=form)


@app.route('/delete/<int:cafe_id>')
def delete_cafe(cafe_id):
    cafe_to_delete = Cafe.query.get(cafe_id)
    db.session.delete(cafe_to_delete)
    db.session.commit()
    return redirect(url_for('cafes'))


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="8080")
