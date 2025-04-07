from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os 
from werkzeug.utils import secure_filename
from flask_migrate import Migrate




app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fishing.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    description = db.Column(db.Text, nullable=True)

class Catch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fish_name = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    length = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)  
    comment = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('catches', lazy=True))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return 'Napačno uporabniško ime ali geslo'
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return 'Uporabniško ime je že zasedeno, poskusite drugo!'
        
        if not username or not password:
            return 'Ime in geslo morata biti vnešena!'

        try:
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))
        except Exception as e:
            return f'Prišlo je do napake pri registraciji: {str(e)}'

    return render_template('register.html')




@app.route('/logout')
def logout():
    session.pop('user_id', None)
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
        new_spot = FishingSpot(
            name=data['name'], 
            latitude=data['latitude'], 
            longitude=data['longitude'], 
            description=data.get('description', '')
        )
        db.session.add(new_spot)
        db.session.commit()
        return jsonify({'message': 'Ribolovna lokacija dodana!'}), 201
    
    spots = FishingSpot.query.all()
    return jsonify([{'id': s.id, 'name': s.name, 'latitude': s.latitude, 'longitude': s.longitude, 'description': s.description} for s in spots])

@app.route('/add_spot', methods=['POST'])
def add_spot():
    if 'user_id' not in session:
        return jsonify({'message': 'Potrebna je prijava!'}), 403

    if not request.json:
        return jsonify({'message': 'Neveljavni podatki'}), 400

    data = request.json
    new_spot = FishingSpot(
        name=data['name'],
        latitude=data['lat'],
        longitude=data['lng'],
        description=data.get('description', '')
    )
    db.session.add(new_spot)
    db.session.commit()
    return jsonify({'message': 'Ribolovna lokacija uspešno dodana!'})



@app.route('/buy_vip', methods=['POST'])
def buy_vip():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user:
        user.is_vip = True  
        db.session.commit()
        session['is_vip'] = True
        return redirect(url_for('leaderboard'))

    return "Napaka: Uporabnik ne obstaja", 400