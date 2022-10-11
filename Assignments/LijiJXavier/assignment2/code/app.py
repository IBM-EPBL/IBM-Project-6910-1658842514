from flask import Flask, render_template,request,redirect,url_for,session
import ibm_db
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=2d46b6b4-cbf6-40eb-bbce-6251e6ba0300.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=32328;SECURITY=SSL;SSLservercertificate=DigiCertGlobalRootCA.crt;UID=gth80312;PWD=fEQO2rLE1hFMbDyJ",'','')

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/',methods=['GET', 'POST'])
def Register():
    session['msg']=""
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['newpassword']
        
        sql = "SELECT * FROM Users WHERE email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        
        if account:
            session['msg']= 'Account already exists'
            return redirect(url_for("login"))  
        else:
            insert_sql = "INSERT INTO Users VALUES (?,?,?)"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, name)
            ibm_db.bind_param(prep_stmt, 2, email)
            ibm_db.bind_param(prep_stmt, 3, password)
            ibm_db.execute(prep_stmt)
            session['msg']= 'New account created Login'
            return redirect(url_for("login"))
     
    
    return render_template('signup.html')   

       

    
    

@app.route('/login',methods=['GET', 'POST'])
def login():
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['newpassword']
        
        
        sql = "SELECT * FROM Users WHERE Email =?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_both(stmt)
        
        accounts=account
        
        
        if (account):
            if  (password == accounts['PASSWORD'] ):
                return render_template('Welcome.html',name=account['NAME'])
            else :
                return render_template('signin.html',msg='wrong Password')
        else :
            return render_template('signin.html',msg='wrong credentials')
            
    else:
        return  render_template('signin.html',msg=session['msg'])
    
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/home')
def home():
    return render_template('home.html')


