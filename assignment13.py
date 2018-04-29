#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Week13 Assignment13 flask"""

import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
    abort, render_template, flash
from contextlib import closing


DATABASE = 'hw13.db'
DEBUG = True
SECRET_KEY = '\xbe7\xc2\xfb1\x0e6\xd8\xa8\xf7\x04\xb6\x80\x16f>+6I%7\xce\xd2'
USERNAME = 'admin'
PASSWORD = 'password'

app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'hw13.db', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect('/dashboard')
    return render_template('login.html', error=error)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    cur = g.db.execute('select ID, FIRST_NAME, LAST_NAME from STUDENTS')
    students = [dict(ID=row[0], FIRST_NAME=row[1], LAST_NAME=row[2])
                for row in cur.fetchall()]
    cur1 = g.db.execute('select ID, SUBJECT, NUM_QUESTIONS, QUIZ_DATE from QUIZZES')
    quizzes = [dict(ID=row[0], SUBJECT=row[1], NUM_QUESTIONS=row[2],
                    QUIZ_DATE=row[3]) for row in cur1.fetchall()]
    return render_template('dashboard.html',
                           students=students, quizzes=quizzes)


@app.route('/student/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'GET':
        return render_template('addstudent.html')
    elif request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        g.db.execute('insert into STUDENTS (FIRST_NAME, LAST_NAME) values (?, ?)',
                     [request.form['FIRST_NAME'], request.form['LAST_NAME']])
        g.db.commit()
    flash('New student successfully added')
    return redirect(url_for('dashboard'))


@app.route('/quiz/add', methods=['GET', 'POST'])
def add_quiz():
    if request.method == 'GET':
        return render_template('addquiz.html')
    elif request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        g.db.execute('insert into QUIZZES (SUBJECT, NUM_QUESTIONS, QUIZ_DATE) '
                     'values (?, ?, ?)', [request.form['SUBJECT'],
                                          request.form['NUM_QUESTIONS'],
                                          request.form['QUIZ_DATE']])
        g.db.commit()
    flash('New quiz successfully added')
    return redirect(url_for('dashboard'))


@app.route('/student/<id>', methods=['GET'])
def display_results(id):
    cur2 = g.db.execute('select FIRST_NAME, LAST_NAME from STUDENTS where ID = ?', id)
    stu_names = cur2.fetchall()[0]
    student_name = '{} {}'.format(stu_names[0], stu_names[1])
    cur3 = g.db.execute('select QUIZ_ID, SCORE from RESULTS where STU_ID = ?', id)
    results = [dict(QUIZ_ID=row[0], SCORE=row[1]) for row in cur3.fetchall()]
    render_template('results.html', results=results, student_name=student_name)


@app.route('/results/add', methods=['GET', 'POST'])
def add_result():
    if request.method == 'GET':
        cur4 = g.db.execute('select ID, SUBJECT from QUIZZES')
        quizzes = [dict(quiz_id=row[0], subject=row[1]) for row in cur4.fetchall()]
        cur5 = g.db.execute('select ID, FIRST_NAME, LAST_NAME from STUDENTS')
        students = [dict(student_id=row[0], student_name='{} {}'.format(row[1], row[2]))
                    for row in cur5.fetchall()]
        return render_template('addresults.html', quizzes=quizzes, students=students)
    elif request.method == 'POST':
        g.db.execute("insert into RESULTS (STU_ID, QUIZ_ID, SCORE) values "
                     "(?, ?, ?)", (request.form['STU_ID'],
                                   request.form['QUIZ_ID'], request.form['SCORE']))
        g.db.commit()
        flash("Quiz results updated")
        return redirect('/dashboard')
    else:
        flash("Could Not Update Record")
        return redirect('/results/add')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
