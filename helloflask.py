from flask import Flask, render_template, request, redirect, make_response, session
from datetime import datetime
from flask import g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import math

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///satcounter2.db'
app.config['SQLALCHEMT_ECHO'] = True
app.config['SECRET_KEY'] = 'development-key'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(30), nullable=False)
    messages = db.relationship('Message', backref=db.backref('writer', lazy='joined'), lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return self.username


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    writer_user_id = db.Column(db.Text, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, content, writer_user_id):
        self.content = content
        self.writer_user_id = writer_user_id

    def __repr__(self):
        return '<Message %r>' % self.id


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('satcounter.db')
    return db


@app.before_request
def before_request():
    print(">> before request")
    if 'user_id' in session:
        g.user = User.query.filter_by(id=session['user_id']).first()
    g.delta = getdelta()


@app.teardown_appcontext
def close_connection(expn):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    return


def get_countdown():
    return datetime(2017, 11, 16) - datetime.now()


def getdelta():
    sat_date = datetime(2017, 11, 16)
    now = datetime.now()
    delta = sat_date - now
    return delta


@app.route('/')
def index():
    page = int(request.args.get('page', 1))
    limit = 5
    start = (page - 1) * limit
    end = start + limit
    comments = Message.query.all()
    response = make_response(
        render_template('index.html', page=page, comments=comments[start:end],
                        maxpage=math.ceil(len(comments) / limit)))
    return response


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')


@app.route('/login', methods={'GET', 'POST'})
def login():
    error = False
    if (request.method == 'POST'):
        print(generate_password_hash(request.form['pw']))
        usr = User.query.filter_by(username=request.form['id']).first()
        if usr is None:
            error = True
        elif not check_password_hash(usr.password, request.form['pw']):
            error = True
        else:
            session['user_id'] = usr.id
            return redirect('/')
    print(error)
    return render_template('login.html', error=error)


@app.route('/signup', methods={'GET', 'POST'})
def join():
    if request.method == 'POST':
        usr = User(request.form['id'], generate_password_hash(request.form['pw']))
        db.session.add(usr)
        db.session.commit()
        session['user_id'] = usr.id
        return redirect('/')
    usr = User.query.limit(10).all()
    return render_template('join.html', usrs=usr)


@app.route('/about')
def about():
    return render_template('about.html', comments=comments)


@app.route('/hello')
def hello():
    return "안녕!"


@app.route('/users')
def users():
    return render_template('user_list.html')


@app.route('/users/<int:username>')
def user_profile(username):
    msgs = Message.query.filter_by(writer_user_id=username)
    return render_template('profile.html', msgs=msgs)


@app.route('/articles/<string:number>')
def user_articles(number):
    return "hi"


@app.route('/post_comment', methods={'GET', 'POST'})
def write_comment_form():
    if request.method == 'POST':
        msg = Message(request.form['name'], g.user.id)
        db.session.add(msg)
        db.session.commit()
        return redirect('/')
    return render_template('write.html')


@app.route("/comments/<int:pages>")
def get_comments(pages):
    comments = Message.query.offset(((pages - 1) * 5)).limit(5).all()
    return str(comments)


if __name__ == '__main__':
    app.run(port=8080, debug=True)
