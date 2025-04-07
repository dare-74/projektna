from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fishing.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_vip = db.Column(db.Boolean, default=False)

class FishingSpot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return 'Vnesi uporabniško ime in geslo.'
        if User.query.filter_by(username=username).first():
            return 'Uporabnik že obstaja.'
        hashed_pw = generate_password_hash(password)
        db.session.add(User(username=username, password=hashed_pw))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['is_vip'] = user.is_vip
            return redirect(url_for('index'))
        return 'Napačno uporabniško ime ali geslo.'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/map')
def map_view():
    spots = FishingSpot.query.all()
    return render_template('map.html', spots=spots)

@app.route('/api/spots', methods=['GET', 'POST'])
def fishing_spots():
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'message': 'Potrebna je prijava!'}), 403
        data = request.json
        spot = FishingSpot(
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            description=data.get('description', '')
        )
        db.session.add(spot)
        db.session.commit()
        return jsonify({'message': 'Dodano!'}), 201
    spots = FishingSpot.query.all()
    return jsonify([{
        'id': s.id, 'name': s.name, 'latitude': s.latitude,
        'longitude': s.longitude, 'description': s.description
    } for s in spots])


@app.route('/vip')
def vip():
    return render_template('vip.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
