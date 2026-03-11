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

# ✅ DO NOT load dataset at startup
dataset = None
states = None


def load_dataset():
    global dataset, states
    if dataset is None:
        dataset = pd.read_csv("Dataset/CrimesOnWomenData.csv")
        states = np.unique(dataset['State'])


# ---------------- ROUTE ----------------

def Route(request):
    return render(request, 'Route.html', {})


def RouteAction(request):
    if request.method == 'POST':
        areaname = request.POST.get('t1', False)
        areaname = areaname + " Police Station"
        areaname = areaname.replace(" ", "+")
        output = '<iframe width="800" height="650" src="https://maps.google.com/maps?q='+areaname+'&output=embed"></iframe>'
        context = {'data': output}
        return render(request, 'UserScreen.html', context)


# ---------------- HEATMAP ----------------

def Heatmap(request):

    load_dataset()

    heatmap = dataset.groupby('State')['Rape'].sum().sort_values(ascending=False).reset_index(name="Total Crimes")[0:10]

    labels = heatmap['State'].ravel()
    heatmap.drop(['State'], axis=1, inplace=True)

    heatmap = heatmap.values

    data = []

    for i in range(len(heatmap)):
        values = [0]*10
        values[i] = heatmap[i,0]
        data.append(values)

    heatmap = np.asarray(data)

    ax = sns.heatmap(heatmap, xticklabels=labels, yticklabels=labels, annot=True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    plt.clf()

    context = {'data': 'Heatmap', 'img': img_b64}

    return render(request, 'UserScreen.html', context)


# ---------------- TRAIN ML ----------------

def TrainML(request):

    f = open('model/model_history.pckl', 'rb')
    hist = pickle.load(f)
    f.close()

    plt.plot(hist['accuracy'])
    plt.plot(hist['val_accuracy'])

    buf = io.BytesIO()
    plt.savefig(buf, format='png')

    img_b64 = base64.b64encode(buf.getvalue()).decode()

    plt.clf()

    context = {'data': 'Accuracy Graph', 'img': img_b64}

    return render(request, 'UserScreen.html', context)


# ---------------- CRIME PREDICT ----------------

def CrimePredict(request):

    load_dataset()

    output = '<select name="t1">'

    for s in states:
        output += '<option value="'+s+'">'+s+'</option>'

    output += "</select>"

    context = {'data1': output}

    return render(request, 'CrimePredict.html', context)


def CrimePredictAction(request):

    load_dataset()

    areaname = request.POST.get('t1')

    crime = dataset.loc[dataset['State'] == areaname]

    crime = crime['Rape'].ravel()[0]

    output = "Crime in "+areaname+" = "+str(crime)

    context = {'data': output}

    return render(request, 'UserScreen.html', context)


# ---------------- PANIC ----------------

def Panic(request):
    return render(request, 'Panic.html', {})


def PanicAction(request):

    global username, email

    areaname = request.POST.get('t1')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        connection.login("test@gmail.com", "password")
        connection.sendmail(
            from_addr="test@gmail.com",
            to_addrs=[email],
            msg=username + " emergency from " + areaname
        )

    context = {'data': "Emergency message sent"}

    return render(request, 'Panic.html', context)


# ---------------- LOGIN ----------------

def UserLogin(request):
    return render(request, 'UserLogin.html', {})


def UserLoginAction(request):

    global username, email

    users = request.POST.get('t1')
    password = request.POST.get('t2')

    con = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        database='safety'
    )

    with con:
        cur = con.cursor()
        cur.execute("select username,password,email from register")

        for row in cur.fetchall():

            if row[0] == users and row[1] == password:

                username = users
                email = row[2]

                return render(request, "UserScreen.html", {'data': 'Welcome'})


    return render(request, 'UserLogin.html', {'data': 'Invalid'})


# ---------------- REGISTER ----------------

def Register(request):
    return render(request, 'Register.html', {})


def RegisterAction(request):

    username = request.POST.get('t1')
    password = request.POST.get('t2')
    contact = request.POST.get('t3')
    email = request.POST.get('t4')
    address = request.POST.get('t5')

    con = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        database='safety'
    )

    with con:
        cur = con.cursor()

        cur.execute(
            "INSERT INTO register VALUES(%s,%s,%s,%s,%s)",
            (username, password, contact, email, address)
        )

    return render(request, 'Register.html', {'data': 'Registered'})


# ---------------- INDEX ----------------

def index(request):
    return render(request, 'index.html', {})