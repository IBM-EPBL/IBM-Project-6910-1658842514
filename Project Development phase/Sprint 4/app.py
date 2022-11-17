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
import random
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
IST = pytz.timezone('Asia/Kolkata')



month=datetime.now(IST).month
year =datetime.now(IST).year

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=2d46b6b4-cbf6-40eb-bbce-6251e6ba0300.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=32328;SECURITY=SSL;SSLservercertificate=DigiCertGlobalRootCA.crt;UID=gth80312;PWD=fEQO2rLE1hFMbDyJ",'','')

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

def sendemail(toemail,subject,content):
    message = Mail(
        from_email='xxx',
        to_emails=toemail,
        subject=subject,
        html_content=content)
    try:
        sg = SendGridAPIClient('xxx')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


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
                toemail = email
                subject = "Registration Successful"
                content = "Dear " + str(name) + ''' ,<br><br>Thank you for registering in the application.<br>
                            You have been registered successfully in Personal tracker application. <br><br>Continue enjoying our services and save your money. <br><br>
                            Don't share your login credentials with anyone.<br><br>
                            Regards,<br>
                            Personal expense Tracker.'''
                sendemail(toemail,subject,content)

                print ('email should be sent to' + email)
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
                    session['name']=account['NAME']
                    session['user_id']=account['USER_ID']
                    session['email']=account['EMAIL']
                    session['month']=month
                    session['year']=year
                    session['loggedin']=True
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
    session['loggedin'] = False
    flash('You have been logged out')
    return redirect(url_for("login"))
    
@app.route('/profile',methods=['GET', 'POST'])
def profile():
    if session['loggedin'] :
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
                
                
                return render_template('profile.html',account=account, budget=budget,month=month)
            else:
                flash('Error',error)
                return redirect(url_for("login"))
        
            

    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))

    else:
        return ''' some error occured'''
     
    
@app.route('/dashboard')
def dashboard():
    
    if session['loggedin'] :
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
        if not budget:
            budget = 0
        

        
        
        sql = "SELECT transaction_id,date,description,amount,category,transactions.category_id FROM Transactions INNER JOIN CATEGORIES ON transactions.category_id = categories.category_id  WHERE user_id =? AND MONTH(date)=? AND YEAR(date)=? ORDER BY date DESC"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,month)
        ibm_db.bind_param(stmt,3,year)
        ibm_db.execute(stmt)
        transactionslist=[]
        account = ibm_db.fetch_assoc(stmt)
        while account :
            transactionslist.append(account)
            account = ibm_db.fetch_assoc(stmt)

        
        totaltest=[0,0,0,0,0]
        for transaction in transactionslist :
            totaltest[transaction['CATEGORY_ID'] - 1] += transaction['AMOUNT']
        
        
        
        total=totaltest
        # for i in [0,1,2,3]:
        #     transactions=[]
        #     sql = "SELECT * FROM transactions WHERE user_id = ? AND category_id=? AND MONTH(date)=? AND YEAR(date)=? "
        #     stmt = ibm_db.prepare(conn, sql)
        #     ibm_db.bind_param(stmt,1,user_id)
        #     ibm_db.bind_param(stmt,2,i+1)
        #     ibm_db.bind_param(stmt,3,month)
        #     ibm_db.bind_param(stmt,4,year)
        #     ibm_db.execute(stmt)
        #     transaction = ibm_db.fetch_assoc(stmt)
        #     while transaction :
        #         transactions.append(transaction['AMOUNT'])
        #         transaction = ibm_db.fetch_assoc(stmt)
        #     total.append(sum(transactions))
        # print(total)
            

        summation =sum(total)
        if budget :
            remaining = budget['BUDGET'] - summation
        else:
            remaining = False

        session['remaining']= remaining

        colours=['#ff8e71','#ff3c0b','#ff5125','#ff653e','#f13100']
        
        df = pd.DataFrame({'Categories': ['Rent and EMI', 'Savings', 'Groceries', 'others','Not Set'] ,'Total': total})
        df = df[df['Total']>=1]
        pie_chart = px.pie(df, 
                           values='Total', 
                           names='Categories',
                           color_discrete_sequence=colours,
                           color='Categories',
#                           title='Coronavirus in the USA',
                           hole=0.05,
                           hover_name='Categories',
                           labels={"Total":"Total in Rs","Categories": "Categories"},
                           height=500,
                           width =600,

                          
                            
                          )
        pie_chart.update_layout(
            font_family="Arial",
            font_color="#ff3c0b",
            font_size=16,
            showlegend=False,
            title_font_family="Times New Roman",
            title_font_color="red",
            legend_title_font_color="green",
            # title={
            #     'text': "Pie Chart",
            #     'y':1.0,
            #     'x':0.5,
            #     'xanchor': 'center',
            #     'yanchor': 'top'},
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

            
                
        return render_template('dashboard.html',transactions=transactionslist ,total=total,summation=summation,graphJSON=graphJSON,budget=budget,remaining=remaining,month=month)
    
    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))
    
    
@app.route('/addexpense',methods=['GET', 'POST'])
def addexpense():
    if session['loggedin'] :
        user_id=session['user_id']
        email=session['email'] 
        
        if request.method == 'POST' and request.form['submit'] == 'addexpense':
            date=request.form['date']
            description=request.form['description']
            amount=request.form['amount']
            category_id=request.form['category']
            print(session['remaining'])

            if session['remaining'] :
                if session['remaining'] >= 0 :
                    if session['remaining'] <= int(amount) :
                        toemail = email
                        subject = "Alert !"
                        content = '''Dear '''+str(session['name'])+ ''', <br><br>

                                  <div style="text-align: center;"> You have exceeded your Monthly limit. The amount of Rs. ''' +str(float(amount)-session['remaining'])+ ''' is exceeded from the actual amount. 
                                  Kindly, maintain the expense as per the registered actual limit, or change your actual Limit for monthly expenses.<br><br>

                                  "Save money and Money will safe you."<br><br>
                              </div>

                            Regards,<br>
                            Personal expense Tracker team     '''
                        sendemail(toemail,subject,content)
                        print('send email to ' + session['email'] )

            
            insert_sql = "INSERT INTO transactions (user_id, date, description,amount,category_id) VALUES (?,?,?,?,?);"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, user_id)
            ibm_db.bind_param(prep_stmt, 2, date)
            ibm_db.bind_param(prep_stmt, 3, description)
            ibm_db.bind_param(prep_stmt, 4, amount)
            ibm_db.bind_param(prep_stmt, 5, category_id)
            ibm_db.execute(prep_stmt)
            flash('added expense')
            return redirect(url_for("dashboard")) 
            
            
        return render_template('addexpense.html')
    
    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))
    
    
@app.route('/delete/<int:id>')
def deleteexpense(id):
    if session['loggedin'] :
        user_id=session['user_id']
        
        insert_sql = "DELETE FROM transactions WHERE transaction_id = ?;"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, id)
        ibm_db.execute(prep_stmt)
        flash('Deleted expense')
        return redirect(url_for("dashboard")) 
        
        


@app.route('/modify/<int:id>',methods=['GET', 'POST'])
def modifyexpense(id):
    if session['loggedin'] :
        user_id=session['user_id']
        email=session['email']
        
        sql = "SELECT * FROM transactions WHERE user_id = ? AND transaction_id = ? "
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,id)
        ibm_db.execute(stmt)
        transaction = ibm_db.fetch_assoc(stmt)
        
        if request.method == 'POST' and request.form['submit'] == 'modifyexpense':
            date=request.form['date']
            description=request.form['description']
            amount=request.form['amount']
            category_id=request.form['category']

            if session['remaining'] :
                if session['remaining'] >= 0:
                    if session['remaining'] <= (int(float(amount)) - int(transaction['AMOUNT'])) :
                        toemail = email
                        toemail = email
                        subject = "Alert !"
                        content = '''Dear '''+str(session['name'])+ ''', <br><br>

                                  <div style="text-align: center;"> You have exceeded your Monthly limit. The amount of Rs. ''' +str((int(float(amount)) - int(transaction['AMOUNT']))-session['remaining'])+ ''' is exceeded from the actual amount. 
                                   Kindly, maintain the expense as per the registered actual limit, or change your actual Limit for monthly expenses.<br><br>

                                  "Save money and Money will safe you."<br><br>
                              </div>

                            Regards,<br>
                            Personal expense Tracker team     '''
                        sendemail(toemail,subject,content)
                        print('send email to' + session['email'] )
            
            insert_sql = "UPDATE transactions SET date = ?, description = ?, amount = ?, category_id = ? WHERE transaction_id = ?;"
            prep_stmt = ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(prep_stmt, 1, date)
            ibm_db.bind_param(prep_stmt, 2, description)
            ibm_db.bind_param(prep_stmt, 3, amount)
            ibm_db.bind_param(prep_stmt, 4, category_id)
            ibm_db.bind_param(prep_stmt, 5, id)
            ibm_db.execute(prep_stmt)
            flash('Modified expense')
            return redirect(url_for("dashboard"))
        
        else:
            
            return render_template('modifyexpense.html',transaction=transaction ,id=id)

            
            
    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))
        
        
@app.route('/budget',methods=['POST'])
def budget(): 
    if session['loggedin'] :
    
        user_id=session['user_id']
        email=session['email']
        month=session['month']
        year=session['year']
        date=str(year)+'-'+str(month)+'-'+'01'
        
        newbudget=float(request.form['budget'])      
        sql = "SELECT * FROM budgets WHERE user_id = ? AND date = ? "
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,date)
        ibm_db.execute(stmt)
        budget = ibm_db.fetch_assoc(stmt)

        
        sql = "SELECT amount FROM Transactions WHERE user_id =? AND MONTH(date)=? AND YEAR(date)=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,user_id)
        ibm_db.bind_param(stmt,2,month)
        ibm_db.bind_param(stmt,3,year)
        ibm_db.execute(stmt)
        transactionslist=[]
        amount = ibm_db.fetch_assoc(stmt)
        while amount :
            transactionslist.append(amount['AMOUNT'])
            amount = ibm_db.fetch_assoc(stmt)
        
        print(transactionslist)
        total=sum(transactionslist)

        if  newbudget <= total :
            toemail = email
            subject = "Alert !"
            content = '''Dear '''+str(session['name'])+ ''', <br><br>

                        <div style="text-align: center;"> You have exceeded your Monthly limit. The amount of Rs. ''' +str(total-newbudget)+ ''' is exceeded from the actual amount. 
                        Kindly, maintain the expense as per the registered actual limit, or change your actual Limit for monthly expenses.<br><br>

                        "Save money and Money will safe you."<br><br>
                        </div>

                        Regards,<br>
                        Personal expense Tracker team     '''
            sendemail(toemail,subject,content)

        
        
        if budget:
            sql = "UPDATE budgets SET budget = ? WHERE date =? AND user_id = ?;"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,newbudget)
            ibm_db.bind_param(stmt,2,date)
            ibm_db.bind_param(stmt,3,user_id)
            ibm_db.execute(stmt)
            
            flash('Budget updated')
            return redirect(url_for("profile"))
            
            
        else:
            sql = "INSERT INTO budgets (date, budget,user_id) VALUES (?,?,?);"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt,1,date)
            ibm_db.bind_param(stmt,2,newbudget)
            ibm_db.bind_param(stmt,3,user_id)
            print(user_id)
            ibm_db.execute(stmt)
            
            flash('Budget added')
            return redirect(url_for("profile"))
        
        return redirect(url_for("profile"))
    
    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))
    
@app.route('/switchmonth',methods=['POST'])
def switchmonth():
    if session['loggedin'] :
        user_id=session['user_id']
        
        monthandyear=request.form['monthandyear']
        print(monthandyear)
        month=monthandyear.split('-')[1]
        year=monthandyear.split('-')[0]
        session['month']=month
        session['year']=year

        return redirect(url_for("dashboard")) 
    
    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))

@app.route('/changepassword',methods=['POST'])
def changepassword():
    if session['loggedin'] :
        user_id=session['user_id']
        email=session['email']
        newpassword=request.form['password']
        passwordhash = generate_password_hash(newpassword, "sha256")

        sql = "UPDATE user SET passwordhash = ? WHERE email = ? AND user_id = ?;"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,passwordhash)
        ibm_db.bind_param(stmt,2,email)
        ibm_db.bind_param(stmt,3,user_id)
        ibm_db.execute(stmt)
            
        flash('Password changed')
        return redirect(url_for("profile"))




    if not session['loggedin'] :
        flash('you are not logged in,please log in')
        return redirect(url_for("login"))

@app.route('/forgotpassword',methods=['GET','POST'])
def forgotpassword():
    if session['loggedin'] :
        flash('Logout First')
        return redirect(url_for("profile"))

    else:

        if request.method == 'POST':
            if request.form['submit'] == 'email':
                email=request.form['email']
                sql = "SELECT * FROM user WHERE email =?"
                stmt = ibm_db.prepare(conn, sql)
                ibm_db.bind_param(stmt,1,email)
                ibm_db.execute(stmt)
                account = ibm_db.fetch_assoc(stmt)
                if account :
                    session['name']=account['NAME']
                    session['user_id']=account['USER_ID']
                    session['email']=email
                    session['month']=month
                    session['year']=year
                    otp=random.randint(100001,1000000)
                    session['otp']=str(otp)
                    print(otp)
                    

                    toemail = email
                    subject = "Your OTP for forget password"
                    content = "Hey "+str(session['name'])+''' ,  <br><br>
                                Your OTP is <b> '''+str(otp)+'''</b>  <br><br>
                                <i>)(Change your password when you are directed to Profile page)</i><br><br>
                                Enter this  code  or Enter the email again to resend it. <br><br>
                                If you don't recognize or expect this email, please don't share the above code with anyone.<br><br>
                                Regards,<br>
                                Personal expense Tracker'''
                    sendemail(toemail,subject,content)

                    

                    

                else :
                    flash ('account with email doesnt exist')
                    return redirect(url_for("login"))

            if request.form['submit'] == 'otp':
                otp=request.form['otp']
                if otp == session['otp']:
                    session['loggedin'] = True
                    flash('change your Password');
                    return redirect(url_for("profile"))
                else :
                    print('otp is wrong')
                    flash ('otp is wrong')
                    return render_template('forgotpassword.html')



        return render_template('forgotpassword.html')

    
        




@app.route('/about')
def about():
    # if session['loggedin'] :
        return render_template('aboutloggedin.html')
    # else :
    #     return render_template('aboutloggedoff.html')



        

    
        
#        return render_template('dashboard.html', transactions= False )
#       while transaction :
#            transactions.append(transaction["AMOUNT"])
#            account = ibm_db.fetch_assoc(stmt)
#        total=transactions.sum()
#        print (total)
#        return render_template('dashboard.html')
        

    
#<!--
#        <td><a href="/delete/{{post.id}}" style="color: cadetblue">Delete</a><br>
#            <a href="/edit/{{post.id}}">Edit</a></td>
#-->
    
#INNER JOIN CATEGORIES ON transactions.category_id = categories.category_id


if __name__ == "__main__":
    app.run(host='0.0.0.0')