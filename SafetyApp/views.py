from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
import os
import io
import base64
import matplotlib.pyplot as plt
import pymysql
import pandas as pd
import numpy as np
import pickle
import smtplib
from datetime import date
import seaborn as sns

global username, email
dataset = pd.read_csv("Dataset/CrimesOnWomenData.csv")
states = np.unique(dataset['State'])

def Route(request):
    if request.method == 'GET':
        return render(request, 'Route.html', {})

def RouteAction(request):
    if request.method == 'POST':
        areaname = request.POST.get('t1', False)
        areaname = areaname+" Police Station"
        areaname = areaname.replace(" ","+")
        output = '<iframe width="800" height="650" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.com/maps?q='+areaname+'&amp;ie=UTF8&amp;&amp;output=embed"></iframe><br/>'
        context= {'data':output}
        return render(request, 'UserScreen.html', context)

def Heatmap(request):
    if request.method == 'GET':
        global dataset, states
        heatmap = dataset.groupby('State')['Rape'].sum().sort_values(ascending=False).reset_index(name="Total Crimes")[0:10]
        labels = heatmap['State'].ravel()
        heatmap.drop(['State'], axis = 1,inplace=True)
        heatmap = heatmap.values
        data = []
        for i in range(len(heatmap)):
            values = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            values[i] = heatmap[i,0]
            data.append(values)
        heatmap = np.asarray(data)    
        ax = sns.heatmap(heatmap, xticklabels = labels, yticklabels = labels, annot = True, cmap="viridis" ,fmt ="g");
        ax.set_ylim([0,len(heatmap)])
        plt.title("Women Incident Crime Heatmap")
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        #plt.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.clf()
        plt.cla()
        context= {'data':'Women Incident Crime Heatmap', 'img': img_b64}
        return render(request, 'UserScreen.html', context)

def TrainML(request):
    if request.method == 'GET':
        f = open('model/model_history.pckl', 'rb')
        hist = pickle.load(f)
        f.close()
        plt.figure(figsize=(5,3))
        plt.plot(hist['accuracy'], color = 'blue', label = 'Training Accuracy')
        plt.plot(hist['val_accuracy'], color = 'green', label = 'Validation Accuracy')
        plt.title('Neural Network Accuracy Graph')
        plt.xlabel('Epochs')
        plt.ylabel('Accuracy')
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        #plt.close()
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        plt.clf()
        plt.cla()
        context= {'data':'Neural Network Accuracy Graph', 'img': img_b64}
        return render(request, 'UserScreen.html', context)

def CrimePredict(request):    
    if request.method == 'GET':
        global dataset, states
        output = '<tr><td><font size="3" color="black">Choose&nbsp;State</td><td><select name="t1">'
        for i in range(len(states)):
            output += '<option value="'+states[i]+'">'+states[i]+'</option>'
        output +="</select></td></tr>"
        context= {'data1':output}
        return render(request, 'CrimePredict.html', context)

def CrimePredictAction(request):
    if request.method == 'POST':
        global dataset
        areaname = request.POST.get('t1', False)
        crime = dataset.loc[dataset['State'] == areaname]
        crime = crime['Rape'].ravel()[0]
        output = "<font size=3 color=blue>Predicted Number of Crimes on Women in "+areaname+" = "+str(crime)+"</font>"
        context= {'data':output}
        return render(request, 'UserScreen.html', context)

def Panic(request):
    if request.method == 'GET':
        return render(request, 'Panic.html', {})

def PanicAction(request):
    if request.method == 'POST':
        global username, email
        areaname = request.POST.get('t1', False)
        em = []
        em.append(email)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
            email_address = 'kaleem202120@gmail.com'
            email_password = 'xyljzncebdxcubjq'
            connection.login(email_address, email_password)
            connection.sendmail(from_addr="kaleem202120@gmail.com", to_addrs=em, msg=username+" sent emergency message from location "+areaname+" to you.")
        context= {'data':"Emergency message sent to registered E-Mail"}
        return render(request, 'Panic.html', context)    

def UserLoginAction(request):
    global username
    if request.method == 'POST':
        global username, email
        status = "none"
        users = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'safety',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username,password,email FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == users and row[1] == password:
                    email = row[2]
                    username = users
                    status = "success"
                    break
        if status == 'success':
            context= {'data':'Welcome '+username}
            return render(request, "UserScreen.html", context)
        else:
            context= {'data':'Invalid username'}
            return render(request, 'UserLogin.html', context)

def RegisterAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        email = request.POST.get('t4', False)
        address = request.POST.get('t5', False)
               
        output = "none"
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'safety',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select username FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username:
                    output = username+" Username already exists"
                    break                
        if output == "none":
            db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = 'root', database = 'safety',charset='utf8')
            db_cursor = db_connection.cursor()
            student_sql_query = "INSERT INTO register VALUES('"+username+"','"+password+"','"+contact+"','"+email+"','"+address+"')"
            db_cursor.execute(student_sql_query)
            db_connection.commit()
            print(db_cursor.rowcount, "Record Inserted")
            if db_cursor.rowcount == 1:
                output = "Signup process completed. Login to perform Emergency activities"
        context= {'data':output}
        return render(request, 'Register.html', context)       

def UserLogin(request):
    if request.method == 'GET':
       return render(request, 'UserLogin.html', {})

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})



    

