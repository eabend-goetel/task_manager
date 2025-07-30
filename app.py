from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import db, Person, Priority, Status, Task, Planning
from datetime import date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'changeme'

db.init_app(app)

@app.before_first_request
def setup():
    if not os.path.exists('tasks.db'):
        db.create_all()
        seed_data()

# Seed with sample data

def seed_data():
    if not Person.query.first():
        db.session.add(Person(name='Alice'))
        db.session.add(Person(name='Bob'))
        db.session.commit()
    if not Priority.query.first():
        db.session.add(Priority(name='Low', color='success'))
        db.session.add(Priority(name='Medium', color='warning'))
        db.session.add(Priority(name='High', color='danger'))
        db.session.commit()
    if not Status.query.first():
        db.session.add(Status(name='Open', color='primary'))
        db.session.add(Status(name='In Progress', color='info'))
        db.session.add(Status(name='Done', color='secondary'))
        db.session.commit()

# Utility: weeks start date-end date
from datetime import datetime, timedelta

def week_range(year, week):
    d = datetime.strptime(f'{year}-W{int(week)}-1', "%Y-W%W-%w")
    return d.date(), d.date() + timedelta(days=6)

@app.context_processor
def inject_enums():
    return dict(persons=Person.query.all(), priorities=Priority.query.all(),
                statuses=Status.query.all())

@app.route('/')
def dashboard():
    kw = request.args.get('kw')
    person_id = request.args.get('person')
    tasks = Task.query
    if person_id:
        tasks = tasks.filter(Task.responsible_id==person_id)
    if kw:
        # Filter by KW using planning join
        tasks = tasks.join(Planning).filter(Planning.week==kw)
    tasks = tasks.all()

    # workload calculation
    workload = []
    if kw:
        entries = Planning.query.filter_by(week=int(kw)).all()
        by_person = {}
        for e in entries:
            by_person.setdefault(e.person.name, 0)
            by_person[e.person.name] += e.hours
        for name, hrs in by_person.items():
            workload.append({'name':name,'hours':hrs,'over':hrs>38.5})
    return render_template('dashboard.html', tasks=tasks, workload=workload, kw=kw)

@app.route('/tasks')
def tasks_view():
    tasks = Task.query.all()
    return render_template('tasks.html', tasks=tasks)

@app.route('/task/new', methods=['GET','POST'])
@app.route('/task/<int:task_id>', methods=['GET','POST'])
def edit_task(task_id=None):
    task = Task.query.get(task_id) if task_id else Task()
    if request.method=='POST':
        task.project = request.form['project']
        task.description = request.form['description']
        task.responsible_id = request.form.get('responsible') or None
        task.priority_id = request.form.get('priority') or None
        task.status_id = request.form.get('status') or None
        task.due_date = request.form['due_date'] or None
        if not task.id:
            db.session.add(task)
        db.session.commit()
        flash('Gespeichert')
        return redirect(url_for('tasks_view'))
    return render_template('task_form.html', task=task)

@app.route('/task/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Gelöscht')
    return redirect(url_for('tasks_view'))

@app.route('/planning')
def planning_view():
    entries = Planning.query.all()
    return render_template('planning.html', entries=entries)

@app.route('/planning/new', methods=['GET','POST'])
@app.route('/planning/<int:eid>', methods=['GET','POST'])
def edit_planning(eid=None):
    entry = Planning.query.get(eid) if eid else Planning()
    if request.method=='POST':
        entry.task_id = request.form['task']
        entry.person_id = request.form['person']
        entry.year = int(request.form['year'])
        entry.week = int(request.form['week'])
        entry.hours = float(request.form['hours'])
        if not entry.id:
            db.session.add(entry)
        db.session.commit()
        return redirect(url_for('planning_view'))
    years = list(range(date.today().year-1, date.today().year+2))
    start,end = (None,None)
    if entry.year and entry.week:
        start,end = week_range(entry.year, entry.week)
    return render_template('planning_form.html', entry=entry, tasks=Task.query.all(), years=years, start=start,end=end)

@app.route('/planning/delete/<int:eid>', methods=['POST'])
def delete_planning(eid):
    entry = Planning.query.get_or_404(eid)
    db.session.delete(entry)
    db.session.commit()
    return redirect(url_for('planning_view'))

@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method=='POST':
        table = request.form['table']
        name = request.form['name']
        color = request.form.get('color','')
        model = {'person':Person,'priority':Priority,'status':Status}[table]
        model_entry = model(name=name)
        if hasattr(model_entry,'color'):
            model_entry.color = color
        db.session.add(model_entry)
        db.session.commit()
        return redirect(url_for('settings'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True)
