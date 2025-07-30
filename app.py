import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

DB_FILE = 'app.db'
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

class Priority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default='primary')

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    color = db.Column(db.String(20), default='secondary')

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(400))
    responsible_id = db.Column(db.Integer, db.ForeignKey('worker.id'))
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'))
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))
    due_date = db.Column(db.Date)

    responsible = db.relationship('Worker')
    priority = db.relationship('Priority')
    status = db.relationship('Status')

class Planning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'))
    year = db.Column(db.Integer, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Float, nullable=False)

    task = db.relationship('Task')
    worker = db.relationship('Worker')

# Initialize DB with some defaults
@app.before_first_request
def init_db():
    if not os.path.exists(DB_FILE):
        db.create_all()
        db.session.add(Worker(name='Max Mustermann'))
        db.session.add(Priority(name='Normal', color='primary'))
        db.session.add(Status(name='Offen', color='secondary'))
        db.session.commit()

# Routes
@app.route('/')
def dashboard():
    week = request.args.get('week')
    worker_id = request.args.get('worker')
    tasks = Task.query
    if worker_id:
        tasks = tasks.filter_by(responsible_id=worker_id)
    tasks = tasks.all()
    workers = Worker.query.all()
    return render_template('dashboard.html', tasks=tasks, workers=workers)

@app.route('/tasks')
def tasks():
    tasks = Task.query.all()
    return render_template('tasks.html', tasks=tasks)

@app.route('/tasks/new', methods=['GET', 'POST'])
def task_new():
    if request.method == 'POST':
        task = Task(
            project=request.form['project'],
            description=request.form['description'],
            responsible_id=request.form['responsible'],
            priority_id=request.form['priority'],
            status_id=request.form['status'],
            due_date=request.form['due_date'] or None
        )
        if task.due_date:
            task.due_date = datetime.strptime(task.due_date, '%Y-%m-%d').date()
        db.session.add(task)
        db.session.commit()
        return redirect(url_for('tasks'))
    workers = Worker.query.all()
    priorities = Priority.query.all()
    statuses = Status.query.all()
    return render_template('task_form.html', workers=workers, priorities=priorities, statuses=statuses)

@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
def task_edit(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.project = request.form['project']
        task.description = request.form['description']
        task.responsible_id = request.form['responsible']
        task.priority_id = request.form['priority']
        task.status_id = request.form['status']
        due = request.form['due_date'] or None
        if due:
            task.due_date = datetime.strptime(due, '%Y-%m-%d').date()
        else:
            task.due_date = None
        db.session.commit()
        return redirect(url_for('tasks'))
    workers = Worker.query.all()
    priorities = Priority.query.all()
    statuses = Status.query.all()
    return render_template('task_form.html', task=task, workers=workers, priorities=priorities, statuses=statuses)

@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
def task_delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('tasks'))

@app.route('/planning')
def planning():
    items = Planning.query.all()
    return render_template('planning.html', items=items)

@app.route('/planning/new', methods=['GET', 'POST'])
def planning_new():
    if request.method == 'POST':
        plan = Planning(
            task_id=request.form['task'],
            worker_id=request.form['worker'],
            year=request.form['year'],
            week=request.form['week'],
            hours=request.form['hours'],
        )
        db.session.add(plan)
        db.session.commit()
        return redirect(url_for('planning'))
    tasks = Task.query.all()
    workers = Worker.query.all()
    return render_template('planning_form.html', tasks=tasks, workers=workers)

@app.route('/planning/delete/<int:item_id>', methods=['POST'])
def planning_delete(item_id):
    item = Planning.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('planning'))

@app.route('/masterdata', methods=['GET', 'POST'])
def masterdata():
    if request.method == 'POST':
        table = request.form['table']
        name = request.form['name']
        color = request.form.get('color')
        if table == 'worker':
            db.session.add(Worker(name=name))
        elif table == 'priority':
            db.session.add(Priority(name=name, color=color or 'primary'))
        elif table == 'status':
            db.session.add(Status(name=name, color=color or 'secondary'))
        db.session.commit()
        return redirect(url_for('masterdata'))
    workers = Worker.query.all()
    priorities = Priority.query.all()
    statuses = Status.query.all()
    return render_template('masterdata.html', workers=workers, priorities=priorities, statuses=statuses)

@app.route('/masterdata/edit/<table>/<int:item_id>', methods=['GET', 'POST'])
def masterdata_edit(table, item_id):
    model_map = {
        'worker': Worker,
        'priority': Priority,
        'status': Status,
    }
    model = model_map.get(table)
    if not model:
        return redirect(url_for('masterdata'))
    item = model.query.get_or_404(item_id)
    if request.method == 'POST':
        item.name = request.form['name']
        if hasattr(item, 'color'):
            color = request.form.get('color') or ('primary' if table == 'priority' else 'secondary')
            item.color = color
        db.session.commit()
        return redirect(url_for('masterdata'))
    return render_template('masterdata_form.html', table=table, item=item)

@app.route('/masterdata/delete/<table>/<int:item_id>', methods=['POST'])
def masterdata_delete(table, item_id):
    model_map = {
        'worker': Worker,
        'priority': Priority,
        'status': Status,
    }
    model = model_map.get(table)
    if not model:
        return redirect(url_for('masterdata'))
    item = model.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('masterdata'))

if __name__ == '__main__':
    app.run(debug=True)
