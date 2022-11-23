from flask import Flask, render_template, abort, request, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from os import path
from datetime import datetime
from courses import cs_courses
import random, string

print("Starting app")
app = Flask(__name__)

print("Setting up DB")
basedir = path.abspath(path.dirname(__file__))
dbpath = path.join(basedir, 'database.db')
DB_NAME = 'database.db'

app.config['SQLALCHEMY_DATABASE_URI'] = \
   'sqlite:///' + dbpath
db = SQLAlchemy(app)
db.init_app(app)

### ===== MODEL DEFINITIONS ===== ####
class Course(db.Model): 
   id = db.Column(db.Integer, primary_key=True)
   code = db.Column(db.Integer, nullable=False)
   name = db.Column(db.String(50))
   posts = db.relationship('Comment', lazy='dynamic')

   def __repr__(self):
          return f'<Course CS {self.code}>'

class Upvote(db.Model):
   id = db.Column(db.Integer, primary_key=True, autoincrement=True)
   value = db.Column(db.Integer)
   comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
   user_cookie = db.Column(db.String(10))

class Comment(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   body = db.Column(db.String(1000))
   timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
   course = db.Column(db.Integer, db.ForeignKey('course.code'))
   upvotes = db.relationship(Upvote)
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

if not path.exists(DB_NAME):
   db.create_all(app=app)
   populate()
   print('Created database')
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
      resp = make_response(redirect(url_for('course', course_code=course_code)))
      if 'comment' in request.form:
         body = request.form['comment']
         comment_obj = Comment(
            body=body,
            course=course_code
         )
         db.session.add(comment_obj)
         db.session.commit()
      else:
         upvoted_comment = int(request.form['comment_id'])
         value = int(request.form['value'])
         if not request.cookies.get('session_id'):
            letters = string.ascii_letters
            cookie_id = ''.join(random.choice(letters) for i in range(10))
            resp.set_cookie('session_id', cookie_id)
         else:
            cookie_id = request.cookies.get('session_id')
            existing_upvote = Upvote.query.filter_by(user_cookie=cookie_id, comment_id=upvoted_comment).first()
            if existing_upvote:
               if existing_upvote.value != value:
                  existing_upvote.value = value
                  db.session.commit()
               return resp  
         new_upvote = Upvote(value=value, comment_id=upvoted_comment, user_cookie=cookie_id)
         db.session.add(new_upvote)
         db.session.commit()
      return resp

   course = Course.query.filter_by(code=course_code).first()   
   if not course:
      abort(404)
   comments = Comment.query.order_by(desc(Comment.timestamp)).filter_by(course=course_code)
   return render_template('course.html', course=course, comments=comments)

### ===== END OF ROUTES ===== ###

if __name__ == '__main__':
    app.run(host="localhost", port=8000, debug=True)