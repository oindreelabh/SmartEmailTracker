"""
Flask Application to start Smart Email Tracker
python start.py
on localhost:5000
"""
import csv
import os
import time
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_login import LoginManager, login_user, UserMixin, current_user, \
login_required, logout_user
from werkzeug.utils import secure_filename
from xgb_inp import inp
from file_parser import allowed_ext, extract_text
from listener_xg import handle_new_email
from Glove_XGBoost import train



date_ = datetime.today().ctime()


app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mails.sqlite3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///User.db'
app.config['SECRET_KEY'] = "random string"
app.config['UPLOAD_FOLDER'] = "uploads"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


class User(db.Model, UserMixin):
    """
    user database definition
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}','{self.password}')"


@login_manager.user_loader
def load_user(user_id):
    """
    load user
    """
    return User.query.get(int(user_id))


class RegistrationForm(FlaskForm):
    """
    registration form
    """
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = StringField('Password',
                           validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = StringField('Confirm Password',
                                   validators=[DataRequired(),
                                               EqualTo('password')])
    submit = SubmitField('SignUp')

    def validate_username(self, username):
        """
        username validation
        """
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. \
                                   Please choose a different username')

    def validate_email(self, email):
        """
        email validation
        """
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already taken. \
                                   Please choose a different email-address')


class LoginForm(FlaskForm):
    """
    login form
    """
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = StringField('Password',
                           validators=[DataRequired(), Length(min=6, max=20)])
    submit = SubmitField('SignIn')
    remember = BooleanField('Remember Me')


class mails(db.Model):
    """
    email table definition
    """
    id = db.Column('mail_id', db.Integer, primary_key=True)
    mfrom = db.Column(db.String(50))
    mto = db.Column(db.String(50))
    mdate = db.Column(db.String(20))
    msubject = db.Column(db.String(200))
    mbody = db.Column(db.String(500))
    m_class = db.Column(db.String(50))
    ID = db.Column(db.String(50))


def __init__(self, mfrom, mto, mdate, msubject, ID, mbody, m_class):
    """
    definition of mail object
    """
    self.mfrom = mfrom
    self.mto = mto
    self.mdate = mdate
    self.msubject = msubject
    self.mbody = mbody
    self.m_class = m_class
    self.ID = ID


def write_mail(mail):
    """
    create txt copy of form mail
    """
    timestr = time.strftime("%Y%m%d-%H%M%S")
    fname = "./inputEmails/email_" + str(timestr) + '.txt'
    f = open(fname, "w+")
    f.write("To: %s \n" % mail.mto)
    f.write("From: %s \n" % mail.mfrom)
    f.write("Subject: %s \n\n" % mail.msubject)
    f.write("%s \n" % mail.mbody)
    #f.write("Email_Body: %s \n" % mail.mbody)
    #f.write("Transaction ID: %s \n" % mail.ID)
    #f.write("Class: %s \n" % mail.m_class)
    #f.write("Date: %s \n" % mail.mdate)
    print(mail.m_class)
    f.close()


@app.route('/upload')
def upload_file():
    """
    renders page to upload email as a file
    """
    return render_template('upload.html')

@app.route('/retrain')
def retrain():
    """
    retrain model only if at least 40 mails of new classes
    """
    #define 3 sets of classes
    org_classes = {'Complete', 'Failed', 'Request', 'General', 'Pending', 'Processing'}
    new_classes = set()
    new_classes_40 = set()
    ctr = 0
    for mail in mails.query.all():
        mail.m_class = str(mail.m_class).capitalize()
        if mail.m_class not in org_classes:
            new_classes.add(mail.m_class)
    db.session.commit()
    for mail in mails.query.all():
        if mail.m_class in new_classes and mails.query.filter(mails.m_class == mail.m_class).count() > 39:
            new_classes_40.add(mail.m_class)
    with open('emaildataset.csv', 'a') as f:
        f.write('\n')
        f.close()
    with open('emaildataset.csv', 'a') as f:
        out = csv.writer(f)
        for mail in mails.query.all():
            if mail.m_class in org_classes or mail.m_class in new_classes_40:
                ctr += 1
                out.writerow([mail.mfrom, mail.mto, mail.msubject, mail.mbody, mail.ID, mail.mdate, mail.m_class])
                db.session.delete(mail)
                db.session.commit()
        f.close()
    if ctr > 0:
        msg = '' + str(ctr) + ' mail(s) sent for retraining successfully!'
        train()
    else:
        msg = 'Less than 40 emails of new classes - model not retrained.'
    return render_template('retrained.html', message=msg)


'''
@app.route('/retrain')
def retrain():
    """
    append DB emails to training dataset
    call model from retraining
    """
    with open('emaildataset.csv', 'a+') as f:
        f.write('\n')
        f.close()
        with open('emaildataset.csv', 'a+') as f:
            out = csv.writer(f)
            ct = 0
            for mail in mails.query.all():
                out.writerow([mail.mfrom, mail.mto, mail.msubject, mail.mbody, mail.ID,
                              mail.mdate, mail.m_class])
                ct = ct +1
            db.session.query(mails).delete()
            db.session.commit()
            f.close()
            msg = '' + str(ct) + ' mail(s) sent for retraining successfully!'
        # run model again
        train()
    return render_template('retrained.html', message=msg)
'''

@app.route('/show')
@login_required
def show_all():
    """
    display all emails currently in DB
    """
    #return render_template('show_all.html',
    # mails=mails.query.filter(mails.mto == current_user.email).all())
    return render_template('show_all.html',
                           mails=mails.query.order_by(mails.id.desc()).all())


@app.route("/", methods=["GET", "POST"])
def welcome():
    """
    homepage
    accept email with attachment from UI form
    predict and display output class
    """
    global my_dict, mclass, tid
    if request.method == "POST":
        my_dict = inputvalues = {
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
            body1 = extract_text(app.config['UPLOAD_FOLDER'] + '/' + fullname)

            if body1 != "":
                body1 = '\n-----------Extracted from Attachment-----------\n' + body1

        #append attchment txt to message body for prediction
        inputvalues['Message'] = inputvalues['Message'] + str(body1)
        print(inputvalues['Message'])


        if (inputvalues['Subject'] == "" and inputvalues['Message'] == ""):
            msg = 'Empty email or invalid attachment - no prediction!'
            return render_template('retrained.html', message=msg)

        m_class, ID, amt = inp(inputvalues['To'], inputvalues['From'],
                          inputvalues['Subject'], inputvalues['Message'])
        mclass = m_class
        tid = ID
        return render_template("index1.html", m=m_class)

    else:
        return render_template("index1.html")


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file_1():
    """
    upload email as a file
    pdf, txt, image
    """
    global my_dict, mclass, tid
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
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], fullname))
        #f.save("./inputEmails/" + fullname)

        #if not allowedExt('inputEmails/' + fullname):
        if not allowed_ext(os.path.join(app.config['UPLOAD_FOLDER'], fullname)):
            msg = 'Invalid file type - no prediction!'
            return render_template('retrained.html', message=msg)


        to_add, from_add, received_date, sub, id, body, m_class = handle_new_email(os.path.join(app.config['UPLOAD_FOLDER'], fullname))
        my_dict = {
            "From": from_add,
            "To": to_add,
            "Subject": sub,
            "Message": body,
            "Date": received_date
        }
        mclass = m_class
        tid = id
        return render_template("index1.html", m=m_class)

    else:
        return render_template("index1.html")


@app.route('/newclass', methods=['GET', 'POST'])
def new_class():
    """
    manually correct predicted class
    can enter a new class also
    """
    if request.method == "POST":
        mclass = str(request.form['NewClass'])
        mail = mails()
        __init__(mail, my_dict['From'], my_dict['To'], my_dict['Date'],
                 my_dict['Subject'], tid, my_dict['Message'], mclass)
        #write_mail(mail)
        db.session.add(mail)
        db.session.commit()
        # time.sleep(4)
        flash('Record was successfully added')
        return render_template("index1.html")
    else:
        return render_template("new_class.html")


@app.route('/wrong', methods=['GET', 'POST'])
def wrong():
    """
    if predicted class is wrong
    input new class
    add to DB
    """
    if request.method == "POST":
        mclass = str(request.form.get("class", None))
        if mclass == 'newclass':
            return redirect(url_for('new_class'))
        #mclass = mclass.capitalize()
        #print(mclass)
        mail = mails()
        __init__(mail, my_dict['From'], my_dict['To'], my_dict['Date'],
                 my_dict['Subject'], tid, my_dict['Message'], mclass)
        #write_mail(mail)
        db.session.add(mail)
        db.session.commit()
        #time.sleep(4)
        flash('Record was successfully added')
        return redirect(url_for('show_all'))
    else:
        return render_template("dropdown.html")


@app.route('/right')
def right():
    """
    if predicted class is right, add mail to DB
    """
    mail = mails()
    __init__(mail, my_dict['From'], my_dict['To'], my_dict['Date'],
             my_dict['Subject'], tid, my_dict['Message'], mclass)
    #write_mail(mail)
    db.session.add(mail)
    db.session.commit()
    time.sleep(4)
    flash('Record was successfully added')
    return redirect(url_for('welcome'))


@app.route('/thread', methods=['GET', 'POST'])
@login_required
def findthread():
    """
    find all emails with particular transaction id
    """
    if request.method == "POST":
        id = str(request.form['transacid'])
        return render_template('show_all.html', mails=mails.query.filter(mails.ID == id and mails.mto == current_user.email).all())
    else:
        return render_template('findthread.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    user login
    """
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
    """
    logout current signed in user, redirect to homepage
    """
    logout_user()
    return redirect(url_for('welcome'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Register - create a new account
    """
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
