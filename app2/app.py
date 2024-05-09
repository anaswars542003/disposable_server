from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_mysqldb import MySQL
from hashlib import sha256
import MySQLdb.cursors
import re
import randomname

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'mail_lookup'
app.config['MYSQL_PASSWORD'] = 'mail_lookup'
app.config['MYSQL_DB'] = 'mailserver'

mysql = MySQL(app)

@app.route('/')
@app.route('/login',methods = ['GET','POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        password = sha256(password.encode('utf-8'))
        password = password.hexdigest()
        
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s',(username,password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            session['dis_id'] = ''
            msg = 'Logged in successfully !'
            return redirect(url_for("user", usr = session['username']))
        else:
            msg = 'Incorrect username/password !'
    
    return render_template('login.html',msg = msg)

@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('id',None)
    session.pop('username',None)
    session.pop('dis_id',None)
    return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        password = password.encode('utf-8')
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, SHA2(% s,256) , % s)', (username, password, email, ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('register.html', msg = msg)




@app.route("/<usr>" , methods = ['POST','GET'])
def user(usr):
    if usr in session['username']:
        if request.method == "GET":
            return render_template('user.html',usr = usr)
                                                   # return for list url
        elif request.method == "POST" and 'list' in request.form:
            return redirect(url_for('list',usr=session['username']))
    else:
        abort(404)


@app.route("/generator", methods = ['POST'])
def generator():
        dis_id = randomname.generate_random_name()
        session['dis_id'] = dis_id
        username = session['username']
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = % s', (username,))
        gen_id =  cursor.fetchone()
        tar_id = gen_id['id']
        cursor.execute('INSERT INTO des_aliases VALUES (% s,  % s, 1)',(dis_id,tar_id))
        mysql.connection.commit()
        return redirect(url_for("generate",usr = session['username']))



@app.route("/<usr>/generate", methods = ['GET', 'POST'])
def generate(usr):
    if(usr in session['username'] and 'dis_id' in session.keys()):
        return render_template('generate.html',dis_id = session['dis_id'])
    else:
        abort(404)


@app.route("/<usr>/list", methods =['POST','GET'])
def list(usr):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM des_aliases WHERE for_id=% s',(session['id'],))
    des_ids = cursor.fetchall();

    if request.method == "POST":
        for key in request.form:
            if key.startswith('revert'):
                num = re.sub("^" + 'revert', "", key)
                num = int(num)
                flag = des_ids[num]['allow']
                print (flag)
                if flag == 1:
                    flag = 0
                else:
                    flag = 1
                cursor.execute('UPDATE des_aliases SET allow = % s WHERE des_id = % s',(flag , des_ids[num]['des_id']))
                mysql.connection.commit()
        return redirect(url_for('list',usr=session['username']))
                    
    return render_template('list.html',des_ids=des_ids, length = len(des_ids))





if __name__ == "__main__":
    app.run(debug=True)


