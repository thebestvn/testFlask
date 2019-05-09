from flask import (
	Blueprint, flash, g, session, redirect, render_template, request, url_for
)
from flask.json import jsonify
from werkzeug.exceptions import abort

from ssms.auth import login_required
from ssms.db import get_db

bp = Blueprint('info', __name__)

@bp.route('/')
@login_required
def index(check_author=True):
	"""Get a post and its author by id.

	Checks that the sid exists and optionally that the current user is
	the student.

	:param sid: sid of score to get
	:param check_author: require the current user to be the student
	:return: the score info with student information
	:raise 403: if the current user isn't the student
	"""
	sid = session['sid']
	score = get_db().execute(
		'SELECT cname, courseterm, coursepoint, score'
		' FROM studentCourse sc JOIN course c ON sc.cid = c.cid'
		' WHERE sc.sid = ?',
		(sid,)
	).fetchall()

	if score is None:
		abort(404, "Student id {0} doesn't have Course score.".format(sid))

	#if check_author and score['sid'] != g.user['sid']:
	#	 abort(403)

	return render_template('info/index.html', scores=score)

@bp.route('/getScore', methods=('GET', 'POST'))
# @login_required
def getScore():
	sid = session['sid']
	cate = request.form['cate']
	term = request.form['term']
	scores = get_db().execute(
		'select courseName, score, GPA, render, entryStatus from Performances, Courses where studentNo=?'
		'and Performances.courseNo in (select courseNo from Courses where courseCate=? and courseTerm=?) and Performances.courseNo=Courses.courseNo', (sid, cate, term)).fetchall()
	if scores is None:
		abort(404, "Student id {0} doesn't have selected score.".format(sid))
	results = []
	for x in scores:
		results.append({'courseName': x[0], 'score': x[1], 'GPA': x[2], 'rank': x[3], 'entryStatus': x[4]})
	return render_template('info/myScore.html', scores=results)

@bp.route('/myAnalysis', methods=('GET', 'POST'))
@login_required	
def myAnalysis():
	sid = session['sid']
	
	analysis = get_db().execute(
		'select courseTerm, avg(score), max(score), min(score) from Performances, Courses where Performances.courseNo=Courses.courseNo'
		'and studentNo=? group by courseTerm', (sid,)).fetchall()
		
	if analysis is None:
		abort(404, "Student id{0} doesn't have any score.".format(sid))
		
	return jsonify(term = [x[0] for x in analysis], avg = [x[1] for x in analysis], max = [x[2] for x in analysis], min = [x[3] for x in analysis])

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
	"""Create a new post for the current user."""
	if request.method == 'POST':
		cname = request.form['cname']
		score = request.form['score']
		error = None

	if not cname:
		error = 'Course name is required.'
	elif not score:
		error = 'Score is required'

	if error is not None:
		flash(error)
	else:
		db = get_db()
		course = db.execute(
		'SELECT * FROM course WHERE cname = ? ', (cname,)
		).fetchone()
		if course is None:
			error= 'Course do not exist'
			flash(error)
			db.execute(
				'INSERT INTO studentCourse (sid, cid, score)'
				' VALUES (?, ?, ?)',
				(g.user['sid'], course['cid'], score)
			)
			db.commit()
			return redirect(url_for('info.index'))

	return render_template('info/create.html')

@bp.route('/createCourse', methods=('GET', 'POST'))
@login_required
def createCourse():
	"""Create a new post for the current user."""
	if request.method == 'POST':
		cname = request.form['cname']
		courseterm = request.form['courseterm']
		coursepoint = request.form['coursepoint']
		error = None

		if not cname:
			error = 'Course name is required.'
		elif not courseterm:
			error = 'Course term is required'
		elif not courseterm:
			error = 'Course point is required'

		if error is not None:
			flash(error)
		else:
			db = get_db()
			db.execute(
				'INSERT INTO course (cname, courseterm, coursepoint)'
				' VALUES (?, ?, ?)',
				(cname, courseterm, coursepoint)
			)
			db.commit()
			return redirect(url_for('info.index'))

	return render_template('info/createCourse.html')
	

#@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
	"""Update a post if the current user is the author."""
	post = get_post(id)

	if request.method == 'POST':
		title = request.form['title']
		body = request.form['body']
		error = None

		if not title:
			error = 'Title is required.'

		if error is not None:
			flash(error)
		else:
			db = get_db()
			db.execute(
				'UPDATE post SET title = ?, body = ? WHERE id = ?',
				(title, body, id)
			)
			db.commit()
			return redirect(url_for('blog.index'))

	return render_template('blog/update.html', post=post)


#@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
	"""Delete a post.

	Ensures that the post exists and that the logged in user is the
	author of the post.
	"""
	get_post(id)
	db = get_db()
	db.execute('DELETE FROM post WHERE id = ?', (id,))
	db.commit()
	return redirect(url_for('blog.index'))
