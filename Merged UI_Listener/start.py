import csv
import os

from datetime import datetime

date_ = datetime.today().strftime('%Y-%m-%d')

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import time
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, email_validator, ValidationError
from flask_login import LoginManager, login_user, UserMixin, current_user, login_required, logout_user
from word2vec_XGB import inp
from werkzeug.utils import secure_filename
from PDFMinerParser import parsePDF, allowedExt, extractText
from listenerpdfXG import HandleNewEmail
from Glove_XGBoost import train

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User.db'
app.config['SECRET_KEY'] = "random string"
app.config['UPLOAD_FOLDER'] = "inputEmails"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}','{self.password}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = StringField('Password',
                           validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = StringField('Confirm Password',
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('SignUp')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different username')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already taken. Please choose a different email-address')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = StringField('Password',
                           validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('SignUp')
    remember = BooleanField('Remember Me')


class mails(db.Model):
    id = db.Column('mail_id', db.Integer, primary_key=True)
    mfrom = db.Column(db.String(50))
    mto = db.Column(db.String(50))
    mdate = db.Column(db.String(20))
    msubject = db.Column(db.String(200))
    mbody = db.Column(db.String(500))
    m_class = db.Column(db.String(50))
    ID = db.Column(db.String(50))


def __init__(self, mfrom, mto, mdate, msubject, ID, mbody, m_class):
    self.mfrom = mfrom
    self.mto = mto
    self.mdate = mdate
    self.msubject = msubject
    self.mbody = mbody
    self.m_class = m_class
    self.ID = ID


def write_mail(mail):
    timestr = time.strftime("%Y%m%d-%H%M%S")
    f = open("./inputEmails/email_" + str(timestr) + '.txt', "w+")
    f.write("To: %s \n" % mail.mto)
    f.write("From: %s \n" % mail.mfrom)
    f.write("Subject: %s \n\n" % mail.msubject)
    f.write("Email_Body: %s \n" % mail.mbody)
    f.write("class: %s \n" % mail.m_class)
    f.write("Date: %s \n" % mail.mdate)
    f.close()


@app.route('/upload')
def upload_file():
    return render_template('upload.html')


@app.route('/retrain')
def retrain():
    with open('emaildataset.csv', 'a+') as f:
        out = csv.writer(f)
        ct = 0
        for mail in mails.query.all():
            out.writerow([mail.mfrom, mail.mto, mail.msubject, mail.mbody, mail.mdate, mail.m_class])
            ct = ct +1
        db.session.query(mails).delete()
        db.session.commit()
        f.close()
        msg = '' + str(ct) + ' mail(s) sent for retraining successfully!'
        # run model again
        train()
    return render_template('retrained.html', message=msg)


@app.route('/show')
@login_required
def show_all():
    return render_template('show_all.html', mails=mails.query.order_by(mails.id.desc()).all())


@app.route("/", methods=["GET", "POST"])
def welcome():
    global myDict, mclass, tid
    if request.method == "POST":
        myDict = inputvalues = {
            "From": request.form['From'],
            "To": request.form['To'],
            "Subject": request.form['Subject'],
            "Message": request.form['Message'],
            "Date": date_
        }

        #handle file attachment in email from form
        body1 = ""
        if not request.files.get('file', None):
            print('No file uploaded')
        else:
            f = request.files['file']
            print('File Uploaded')

            sfname = (secure_filename(f.filename))
            timestr = time.strftime("%Y%m%d-%H%M%S")
            fullname = str(timestr) + sfname
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fullname))

            #extract text from txt or pdf AND IMAGE, else "" returned
            body1 = extractText(app.config['UPLOAD_FOLDER'] + '/' + fullname)

            if(body1 != ""):
                body1 = '\n-----------Extracted from Attachment-----------\n' + body1

        #append attchment txt to message body for prediction
        inputvalues['Message'] = inputvalues['Message'] + str(body1)
        print(inputvalues['Message'])


        if (inputvalues['Subject'] == "" and inputvalues['Message'] == ""):
            msg = 'Empty email or invalid attachment - no prediction!'
            return render_template('retrained.html', message=msg)

        m_class, ID = inp(inputvalues['To'], inputvalues['From'], inputvalues['Subject'], inputvalues['Message'])
        mclass = m_class
        tid = ID
        return render_template("index1.html", m=m_class)

    else:
        return render_template("index1.html")


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file_1():
    global myDict, mclass, tid
    if request.method == 'POST':

      if not request.files.get('file', None):
        msg = 'No file uploaded'
        return render_template('retrained.html', message=msg)

      f = request.files['file']
      print('File Uploaded=====')
      f = request.files['file']
      sfname = (secure_filename(f.filename))
      timestr = time.strftime("%Y%m%d-%H%M%S")
      fullname = str(timestr) + "_" +  sfname
      f.save("./inputEmails/" + fullname)

      if not allowedExt('inputEmails/' + fullname):
          msg = 'Invalid file type - no prediction!'
          return render_template('retrained.html', message=msg)


      to_add, from_add, receivedDate, sub, id, body, m_class = HandleNewEmail('inputEmails/' + fullname)
      myDict = {
          "From": from_add,
          "To": to_add,
          "Subject": sub,
          "Message": body,
          "Date": receivedDate
      }
      mclass=m_class
      tid=id
      return render_template("index1.html", m=m_class)

    else:
      return render_template("index1.html")


@app.route('/newclass', methods=['Get', 'POST'])
def new_class():
    if request.method == "POST":
        mclass = str(request.form['NewClass'])
        mail = mails()
        __init__(mail, myDict['From'], myDict['To'], myDict['Date'],
                 myDict['Subject'], tid, myDict['Message'], mclass)
        write_mail(mail)
        db.session.add(mail)
        db.session.commit()
        # time.sleep(4)
        flash('Record was successfully added')
        return render_template("index1.html")
    else:
        return render_template("new_class.html")


@app.route('/wrong', methods=['GET', 'POST'])
def wrong():
    if request.method == "POST":
        mclass = str(request.form.get("class", None))
        if mclass == 'newclass':
            return redirect(url_for('new_class'))
        mail = mails()
        __init__(mail, myDict['From'], myDict['To'], myDict['Date'],
                 myDict['Subject'], tid, myDict['Message'], mclass)
        write_mail(mail)
        db.session.add(mail)
        db.session.commit()
        #time.sleep(4)
        flash('Record was successfully added')
        return redirect(url_for('show_all'))
    else:
        return render_template("dropdown.html")


@app.route('/right')
def right():
    mail = mails()
    __init__(mail, myDict['From'], myDict['To'], myDict['Date'],
             myDict['Subject'], tid, myDict['Message'], mclass)
    write_mail(mail)
    db.session.add(mail)
    db.session.commit()
    time.sleep(4)
    flash('Record was successfully added')
    return redirect(url_for('welcome'))


@app.route('/thread', methods = ['GET','POST'])
@login_required
def findthread():
    if request.method == "POST":
        id = str(request.form['transacid'])
        return render_template('show_all.html', mails=mails.query.filter(mails.mdate == id and mails.mto == current_user.email).all())
    else :
        return render_template('findthread.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('welcome'))
        else:
            flash('Login unsuccessful. You have entered incorrect email or password', 'danger')
    return render_template('login.html', title='login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcome'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('welcome'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
