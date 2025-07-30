from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy without app for later init in app.py

db = SQLAlchemy()

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Priority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default="")

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default="")

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    responsible_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'))
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    due_date = db.Column(db.Date, nullable=True)

    responsible = db.relationship('Person')
    priority = db.relationship('Priority')
    status = db.relationship('Status')

class Planning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Float, nullable=False)

    task = db.relationship('Task')
    person = db.relationship('Person')
