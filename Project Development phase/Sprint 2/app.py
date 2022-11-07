from flask import Flask, render_template,request,redirect,url_for,session
import ibm_db
from flask import flash
from werkzeug.security import generate_password_hash,check_password_hash
import pandas as pd
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pytz
IST = pytz.timezone('Asia/Kolkata')



month=datetime.now(IST).month
year =datetime.now(IST).year

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=2d46b6b4-cbf6-40eb-bbce-6251e6ba0300.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=32328;SECURITY=SSL;SSLservercertificate=DigiCertGlobalRootCA.crt;UID=gth80312;PWD=fEQO2rLE1hFMbDyJ",'','')

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route('/',methods=['GET', 'POST'])
def Register():
    if "user_id" not in session :
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['newpassword']
            passwordhash = generate_password_hash(password, "sha256")

            sql = "SELECT * FROM user WHERE email =?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,email)
            ibm_db.execute(stmt)
            account = ibm_db.fetch_assoc(stmt)

            if account:
                flash('Account with email id already exists, Please login or use another email')
                return redirect(url_for("login"))  
            else:
                insert_sql = "INSERT INTO user (name, email, passwordhash) VALUES (?,?,?);"
                prep_stmt = ibm_db.prepare(conn, insert_sql)
                ibm_db.bind_param(prep_stmt, 1, name)
                ibm_db.bind_param(prep_stmt, 2, email)
                ibm_db.bind_param(prep_stmt, 3, passwordhash)
                ibm_db.execute(prep_stmt)
                flash('New account created,Please Login') 
                return redirect(url_for("login"))


        return render_template('register.html')   
    
    else:
        return redirect(url_for("profile")) 
       

    
    

@app.route('/login',methods=['GET', 'POST'])
def login():
    
    if "user_id" not in session :
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['newpassword']        

            sql = "SELECT * FROM User WHERE Email =?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,email)
            ibm_db.execute(stmt)
            account = ibm_db.fetch_both(stmt)






            if (account):
                if  (check_password_hash(account['PASSWORDHASH'],password)):
                    session['user_id']=account['USER_ID']
                    session['month']=month
                    session['year']=year
                    return redirect(url_for("profile"))
                else :
                    flash('Password is wrong')
                    return render_template('login.html')
            else :
                flash('email is wrong')
                return render_template('login.html')
            
    
        else:
            return  render_template('login.html')
    else:
        return redirect(url_for("profile"))        


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for("login"))
    
@app.route('/profile',methods=['GET', 'POST'])
def profile():
    if "user_id" in session :
        user_id=session['user_id']

        if request.method == "GET":
            
            sql = "SELECT * FROM user WHERE user_id =?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,user_id)
            ibm_db.execute(stmt)
            account = ibm_db.fetch_both(stmt)


            if account:
                month=session['month']
                year=session['year']
                date=str(year)+'-'+str(month)+'-'+'01'
                
                sql = "SELECT * FROM budgets WHERE user_id = ? AND date = ? "
                stmt = ibm_db.prepare(conn, sql)
                ibm_db.bind_param(stmt,1,user_id)
                ibm_db.bind_param(stmt,2,date)
                ibm_db.execute(stmt)
                budget = ibm_db.fetch_assoc(stmt)
                print(budget)
                
                return render_template('profile.html',account=account, budget=budget)
            else:
                flash('Error',error)
                return redirect(url_for("login"))
        
            

    if "user_id" not in session :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))

    else:
        return ''' some error occured'''
     
    
@app.route('/dashboard')
def dashboard():
    
    if "user_id" in session :
        user_id=session['user_id']
        
        month=session['month']
        year=session['year']
        date=str(year)+'-'+str(month)+'-'+'01'
                
        sql = "SELECT * FROM budgets WHERE user_id = ? AND date = ? "
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,date)
        ibm_db.execute(stmt)
        budget = ibm_db.fetch_assoc(stmt)
        
        
        sql = "SELECT transaction_id,date,decription,amount,category FROM Transactions INNER JOIN CATEGORIES ON transactions.category_id = categories.category_id  WHERE user_id =? AND MONTH(date)=? AND YEAR(date)=? ORDER BY date DESC"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,month)
        ibm_db.bind_param(stmt,3,year)
        ibm_db.execute(stmt)
        transactions1=[]
        account = ibm_db.fetch_assoc(stmt)
        while account :
            transactions1.append(account)
            account = ibm_db.fetch_assoc(stmt)
        
        
        total=[]
        for i in [0,1,2,3]:
            transactions=[]
            sql = "SELECT * FROM transactions WHERE user_id = ? AND category_id=? AND MONTH(date)=? AND YEAR(date)=? "
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,user_id)
            ibm_db.bind_param(stmt,2,i+1)
            ibm_db.bind_param(stmt,3,month)
            ibm_db.bind_param(stmt,4,year)
            ibm_db.execute(stmt)
            transaction = ibm_db.fetch_assoc(stmt)
            while transaction :
                transactions.append(transaction['AMOUNT'])
                transaction = ibm_db.fetch_assoc(stmt)
            total.append(sum(transactions))
            

        summation =sum(total)
        if budget:
            remaining = budget['BUDGET'] - summation
        else:
            remaining =0
        colours=px.colors.sequential.Reds
        colours.reverse()
        df = pd.DataFrame({'Categories': ['Rent and EMI', 'Savings', 'Groceries', 'others'] ,'Total': total})
        df = df[df['Total']>=1]
        pie_chart = px.pie(df, 
                           values='Total', 
                           names='Categories',
                           color_discrete_sequence=colours,
                           color='Categories',
#                           title='Coronavirus in the USA',
                           hole=0.05,
                           hover_name='Categories',
                           labels={"Total":"Total in Rs"}, 
                           height=700,
                           width=1000
                            
                          )
        pie_chart.update_layout(
            font_family="Arial",
            font_color="red",
            font_size=18,
            title_font_family="Times New Roman",
            title_font_color="red",
            legend_title_font_color="green",
            title={
                'text': "Pie Chart",
                'y':1.0,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Rockwell"
            )
)
        pie_chart.update_traces(textposition='outside', textinfo='label',
                         marker=dict(line=dict(color='#ffffff', width=2)),
                         opacity=0.9, rotation=180,
                         textfont=dict(
                             family="Times New Roman",
                             size=24,
                             color="#000000"
                             ))
        
        
        
        graphJSON = json.dumps(pie_chart, cls=plotly.utils.PlotlyJSONEncoder)

            
                
        return render_template('dashboard.html',transactions=transactions1 ,total=total,summation=summation,graphJSON=graphJSON,budget=budget,remaining=remaining)
    
    if "user_id" not in session :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))
    
    