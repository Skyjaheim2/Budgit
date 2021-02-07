import os
import requests
import hashlib
from flask import Flask, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import and_
from models import *

import datetime
from datetime import date, timedelta, tzinfo, datetime
from math import inf



# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# app.config["SESSION_TYPE"] = "filesystem"
db.init_app(app)

# ENABLE SESSION
# Session(app)
session = {}

class EST(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours = -5)

    def tzname(self, dt):
        return "EST"

    def dst(self, dt):
        return timedelta(0)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/authenticate", methods=["POST"])
def authenticate():
    userName = request.form.get('userName')
    userEmail = request.form.get('userEmail')
    userPassword = hash_password(request.form.get('userPassword'))
    confirmPassword = request.form.get('confirmPassword')

    user = User(name=userName, email=userEmail, password=userPassword)

    if confirmPassword != '':
        # REGISTER
        if user.addUser() == -1:
            return render_template("index.html", alert=True, alertType="warning", alertMessage="You Are Already Registered")
        session["user_id"] = User.query.filter(and_(User.name == userName, User.password == userPassword)).first().id
        session["userName"] = user.name
        session["userPassword"] = user.email
        return redirect(f"/home/{session['user_id']}")
    else:
        # LOGIN
        if not user.validateCredentials():
            return render_template("index.html", alert=True, alertType="danger", alertMessage="You Are Not Registered")
        session["user_id"] = User.query.filter(and_(User.name == userName, User.password == userPassword)).first().id
        session["userName"] = user.name
        return redirect(f"/home/{session['user_id']}")

@app.route("/home/<string:user_id>")
def home(user_id):
    limitQuery = ExpenseLimit.query.filter_by(user_id=int(user_id)).first()
    try:
        expenseLimits = {
            "this-day": limitQuery.day,
            "this-week": limitQuery.week,
            "this-month": limitQuery.month,
            "this-year": limitQuery.year
        }
    except AttributeError:
        expenseLimits = {"this-day":None, "this-week":None, "this-month":None, "this-year":None}

    totalExpenses = {
        "this-day": getTotalExpense("this-day"),
        "this-week": getTotalExpense("this-week"),
        "this-month": getTotalExpense("this-month"),
        "this-year": getTotalExpense("this-year")
    }
    return render_template("home.html", user_id=user_id, user_expense_limits=str(expenseLimits), total_expenses=str(totalExpenses))


@app.route("/getUserInfo", methods=["GET"])
def getUserInfo():
    try:
        user = User.query.get(session['user_id'])
    except KeyError:
        return redirect("/")

    userInfo = {
        'id': user.id,
        'userName': user.name,
        'Email': user.email,
        'phoneNumber': user.phone_number
    }
    return jsonify(userInfo)

@app.route("/updateUserInfo/<string:userID>/<string:infoToUpdate>/<string:newInfo>", methods=["POST"])
def updateUserInfo(userID, infoToUpdate, newInfo):
    user = User.query.get(userID)
    if infoToUpdate == 'userName':
        user.name = newInfo
        db.session.commit()
    elif infoToUpdate == 'userEmail':
        user.email = newInfo
        db.session.commit()
    elif infoToUpdate == 'userPhoneNumber':
        user.phone_number = infoToUpdate
        db.session.commit()
    return ''


@app.route("/addExpense", methods=["POST"])
def addExpend():
    now = datetime.now(EST()).date()
    now = now.strftime("%B %d, %Y")


    expenseName = request.form.get("expenseName")
    expensePrice = request.form.get("expensePrice")
    date = now
    print(date)
    time = getCurrentTime()

    try:
        expense = Expense(item_name=expenseName, item_price=expensePrice, date=date, time=time, user_id=session["user_id"])
    except KeyError:
        return redirect("/")
    expense.addExpense()

    return redirect(f"/home/{session['user_id']}")

@app.route("/editExpense/<string:item_id>/<string:newItemName>/<string:newItemPrice>", methods=["POST"])
def editExpense(item_id, newItemName, newItemPrice):
    try:
        userID = session['user_id']
    except KeyError:
        return redirect("/")
    userExpense = Expense.query.filter(and_(Expense.user_id == userID, Expense.id == item_id)).first()
    # ITEM NAME BEING EDITED
    if newItemPrice == "Empty" and newItemName != "":
        userExpense.item_name = newItemName
        db.session.commit()
    # ITEM PRICE BEING EDITED
    if newItemName == "Empty" and newItemPrice != "":
        userExpense.item_price = float(newItemPrice)
        db.session.commit()
    # BOTH NAME AND PRICE BEING EDITED
    if newItemName != "Empty" and newItemPrice != "Empty":
        userExpense.item_name = newItemName
        userExpense.item_price = float(newItemPrice)
        db.session.commit()
    return ""

@app.route("/deleteExpense/<string:item_id>", methods=["POST"])
def deleteExpense(item_id):
    userExpense = Expense.query.get(item_id)
    db.session.delete(userExpense)
    db.session.commit()
    return ""


@app.route("/getExpenses/<string:period>", methods=["GET"])
def getExpenses(period):
    now = datetime.now(EST()).date()
    now = now.strftime("%B %d, %Y")

    userExpenses = []
    if period == 'all-time':
        expenseQuery = Expense.query.filter_by(user_id = session['user_id']).all()
    elif period == 'this-day':
        expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date == now)).all()
    elif period == 'this-week':
        thisWeek = getThisWeekForQuery()
        expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.in_(thisWeek))).all()
    elif period == 'this-month':
        thisMonth, thisYear = now.split()[0], now.split()[2]
        expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.like(f"%{thisMonth}%"), Expense.date.like(f"%{thisYear}%"))).all()
    elif period == 'this-year':
        thisYear = now.split()[2]
        expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.like(f"%{thisYear}%"))).all()

    for i, expense in enumerate(expenseQuery):
        userExpenses.append({
            "id": expense.id,
            "item_name": expense.item_name,
            "item_price": expense.item_price,
            "date": expense.date,
            "time": expense.time
        })

    return jsonify(userExpenses)

@app.route("/getTotalExpense/<string:period>", methods=["GET"])
def getTotalExpense(period):
    now = datetime.now(EST()).date()
    now = now.strftime("%B %d, %Y")

    totalExpense = 0
    try:
        if period == 'all-time':
            expenseQuery = Expense.query.filter_by(user_id = session['user_id']).all()
        elif period == 'this-day':
            expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date == now)).all()
        elif period == 'this-week':
            thisWeek = getThisWeekForQuery()
            expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.in_(thisWeek))).all()
        elif period == 'this-month':
            thisMonth, thisYear = now.split()[0], now.split()[2]
            expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.like(f"%{thisMonth}%"), Expense.date.like(f"%{thisYear}%"))).all()
        elif period == 'this-year':
            thisYear = now.split()[2]
            expenseQuery = Expense.query.filter(and_(Expense.user_id == session['user_id'], Expense.date.like(f"%{thisYear}%"))).all()
    except KeyError:
        return redirect("/")

    for expense in expenseQuery:
        totalExpense += expense.item_price

    return str(format(totalExpense, ".2f"))



@app.route("/setExpenseLimit/<string:limit>/<string:period>", methods=["POST", "GET"])
def setExpenseLimit(limit, period):
    day = week = month = year = None
    if period == 'this-day':
        day = limit
    elif period == 'this-week':
        week = limit
    elif period == 'this-month':
        month = limit
    elif period == 'this-year':
        year = limit

    try:
        expenseLimit = ExpenseLimit(day=day,week=week,month=month,year=year, user_id=session['user_id'])
    except KeyError:
        return redirect("/")

    expenseLimit.addExpenseLimit(limit, period)
    return ""

@app.route("/getExpenseLimit/<string:userID>/<string:period>/", methods=["GET"])
def getExpenseLimit(userID, period):
    userID = int(userID)
    try:
        if period == 'this-day':
            limitQuery = ExpenseLimit.query.filter_by(user_id = userID).first().day
        elif period == 'this-week':
            limitQuery = ExpenseLimit.query.filter_by(user_id = userID).first().week
        elif period == 'this-month':
            limitQuery = ExpenseLimit.query.filter_by(user_id = userID).first().month
        elif period == 'this-year':
            limitQuery = ExpenseLimit.query.filter_by(user_id = userID).first().year
    except AttributeError:
        return ""

    return str(limitQuery)

@app.route("/account", methods=["GET"])
def account():
    return render_template("account.html")



@app.route("/test")
def test():
    return render_template("test.html")


def getCurrentTime():
    time = datetime.today().strftime("%H:%M %p")
    time = time.split(':')
    hour = int(time[0])
    minute = time[1]
    if hour <= 12:
        pass
    else:
        hour -= 12
    time = f"{hour}:{minute}"
    return time



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def getThisWeekForQuery():
    now = datetime.now(EST()).date()
    now = now.strftime("%B %d, %Y")

    todayDay = getCurrentDay(now)
    monthIndex = getMonthIndex(now)
    currentYear = getCurrentYear(now)
    startOfWeek = getStartOfWeek(currentYear, monthIndex, todayDay)

    if type(startOfWeek) == tuple:
        lastMonthIndex = startOfWeek[1]
        return getWeeks(currentYear, lastMonthIndex, startOfWeek[0])

    return getWeeks(currentYear, monthIndex, startOfWeek)



def getStartOfWeek(currentYear, monthIndex, todayDay, takeLastSunday=False):
    dayTolerance = {}
    foundPositiveTolerance = False
    if not takeLastSunday:
        for sunday in getSundays(currentYear, monthIndex):
            dayTolerance.update({sunday: (todayDay - sunday)})
    else:
        return (getSundays(currentYear, monthIndex - 1)[-1], monthIndex - 1)

    startOfWeek = None
    minTolerance = inf
    for t in dayTolerance:
        if dayTolerance[t] >= 0:
            foundPositiveTolerance = True
        if dayTolerance[t] < minTolerance and dayTolerance[t] >= 0:
            minTolerance = dayTolerance[t]
            startOfWeek = t

    if foundPositiveTolerance:
        return startOfWeek
    else:
        # WE ARE IN A NEW MONTH AND THE START OF THE WEEK IS STILL IN THE PREVIOUS MONTH
        return getStartOfWeek(currentYear, monthIndex, todayDay, takeLastSunday=True)



def getSundays(year, currentMonthIndex: int):
    Sundays = []
    def allsundays(year, currentMonthIndex: int):
       d = date(year, currentMonthIndex, 1)
       d += timedelta(days = 6 - d.weekday())
       while d.month == currentMonthIndex:
          yield d
          d += timedelta(days = 7)

    for d in allsundays(year, currentMonthIndex):
        Sundays.append(d.day)
    return Sundays


def getWeeks(year, monthIndex, day):
    import datetime
    numweeks = 1
    start_date = datetime.datetime(year=year, month=monthIndex, day=day)

    weeks = {}

    offset = datetime.timedelta(days=0)
    for week in range(numweeks):
        this_week = []
        for day in range(7):
            date = start_date + offset
            date = date.strftime("%B %d, %Y")
            this_week.append(date)
            offset += datetime.timedelta(days=1)
        weeks[week] = this_week

    return weeks[0]


def getCurrentDay(now):
    day = now.split()[1]
    return int(day.replace(',', ''))

def getCurrentYear(now):
    year = now.split()[2]
    return int(year)

def getMonthIndex(now):
    currentMonth = now.split()[0]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
              "November", "December"]

    for i, month in enumerate(months, 1):
        if month == currentMonth:
            return i
    return None


def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_password_hash(password, hash):
    if hash_password(password) == hash:
        return True
    return False

if __name__ == '__main__':
    app.run(debug=True)