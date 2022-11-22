from flask import Flask, render_template, abort, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from os import path
from datetime import datetime
from courses import cs_courses

print("Starting app")
app = Flask(__name__)

print("Setting up DB")
basedir = path.abspath(path.dirname(__file__))
dbpath = path.join(basedir, 'database.db')
DB_NAME = 'database.db'

app.config['SQLALCHEMY_DATABASE_URI'] = \
   'sqlite:///' + dbpath
db = SQLAlchemy(app)

### ===== MODEL DEFINITIONS ===== ####
class Course(db.Model): 
   id = db.Column(db.Integer, primary_key=True)
   code = db.Column(db.Integer, nullable=False)
   name = db.Column(db.String(50))
   posts = db.relationship('Comment', lazy='dynamic')

   def __repr__(self):
          return f'<Course CS {self.code}>'

class Comment(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   body = db.Column(db.String(1000))
   timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
   course = db.Column(db.Integer, db.ForeignKey('course.code'))

   def __repr__(self):
      return f'<Post {self.body}>'

### ===== END OF MODEL DEFINITIONS ===== ####

# Run this in 'flask shell' if you need to repopulate the db with courses. 
# $ flask shell
# >>> from app import populate
# >>> populate()
# >>> Course.query.all()
def populate():    
   for code, name in cs_courses.items():
      course_obj = Course(
         code = code,
         name = name
      )    
      db.session.add(course_obj)
   db.session.commit()

print("Server now running.")

### ===== ROUTES ===== ###
# Routes
@app.route("/")
def index():
   courses = Course.query.all()    
   return render_template('index.html', courses=courses)

@app.route("/cs<int:course_code>/", methods=("GET", "POST"))
def course(course_code):
   if request.method == "POST":
      body = request.form['comment']
      comment_obj = Comment(
         body=body,
         course=course_code
      )
      db.session.add(comment_obj)
      db.session.commit()
      return redirect(url_for('course', course_code=course_code))

   course = Course.query.filter_by(code=course_code).first()   
   if not course:
      abort(404)
   comments = Comment.query.order_by(desc(Comment.timestamp)).filter_by(course=course_code)
   return render_template('course.html', course=course, comments=comments)

### ===== END OF ROUTES ===== ###

if __name__ == '__main__':
    app.run(host="localhost", port=8000, debug=True)