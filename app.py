import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import openai

load_dotenv()

# Basic Logging Setup
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'Engineering Lead' or 'Manager'

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager = db.relationship('User', backref=db.backref('reports', lazy=True))

class CalibrationComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    employee = db.relationship('Employee', backref=db.backref('comments', lazy=True))
    comment_type = db.Column(db.String(50), nullable=False) # 'Behavior' or 'Result'
    comment_text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(50))
    classification = db.Column(db.String(50))

def create_mock_data():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Engineering Lead
        lead = User(username='lead', password='password', role='Engineering Lead')
        db.session.add(lead)

        # Managers
        manager1 = User(username='manager1', password='password', role='Manager')
        manager2 = User(username='manager2', password='password', role='Manager')
        db.session.add_all([manager1, manager2])

        # Employees
        emp1 = Employee(name='Alice', manager=manager1)
        emp2 = Employee(name='Bob', manager=manager1)
        emp3 = Employee(name='Charlie', manager=manager2)
        emp4 = Employee(name='David', manager=manager2)
        db.session.add_all([emp1, emp2, emp3, emp4])

        db.session.commit()

from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user.role == 'Engineering Lead':
        employees = Employee.query.all()
    else:
        employees = user.reports

    # Prepare data for 9-box grid
    classification_map = {'Developing': 0, 'Achieving': 1, 'Exceeding': 2}
    grid = [[[] for _ in range(3)] for _ in range(3)]

    employee_performance = []
    for emp in employees:
        latest_behavior = CalibrationComment.query.filter_by(employee_id=emp.id, comment_type='Behavior').order_by(CalibrationComment.id.desc()).first()
        latest_result = CalibrationComment.query.filter_by(employee_id=emp.id, comment_type='Result').order_by(CalibrationComment.id.desc()).first()

        behavior_class = latest_behavior.classification if latest_behavior else 'N/A'
        result_class = latest_result.classification if latest_result else 'N/A'

        emp_data = {
            'employee': emp,
            'behavior': behavior_class,
            'result': result_class
        }
        employee_performance.append(emp_data)

        if behavior_class in classification_map and result_class in classification_map:
            x = classification_map[result_class]
            y = classification_map[behavior_class]
            grid[y][x].append(emp)

    return render_template('dashboard.html', user=user, employees_performance=employee_performance, grid=grid)

import json

def get_openai_analysis(comment):
    app.logger.info(f"Requesting OpenAI analysis for comment: '{comment}'")
    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Analyze the following performance review comment and return ONLY a single valid JSON object with two keys: 'sentiment' (string: 'Positive', 'Neutral', or 'Negative') and 'classification' (string: 'Exceeding', 'Achieving', or 'Developing').\n\nComment: \"{comment}\"\n\nJSON:",
            max_tokens=60,
            temperature=0.2,
        )
        raw_response = response.choices[0].text.strip()
        app.logger.info(f"OpenAI raw response: {raw_response}")

        result = json.loads(raw_response)
        sentiment = result.get('sentiment', 'N/A')
        classification = result.get('classification', 'N/A')

        app.logger.info(f"Successfully parsed sentiment: {sentiment}, classification: {classification}")
        return sentiment, classification
    except json.JSONDecodeError as e:
        app.logger.error(f"Failed to decode JSON from OpenAI response: {e}")
        app.logger.error(f"Raw response was: {raw_response}")
        return "Error", "JSON Parse Error"
    except Exception as e:
        app.logger.error(f"An unexpected error occurred calling OpenAI API: {e}")
        return "Error", "API Call Failed"

from flask import abort

@app.route('/employee/<int:employee_id>/add_comment', methods=['GET', 'POST'])
@login_required
def add_comment(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    user = User.query.get(session['user_id'])

    if user.role == 'Manager' and employee.manager_id != user.id:
        abort(403) # Forbidden

    if request.method == 'POST':
        comment_text = request.form['comment']
        comment_type = request.form['comment_type']

        sentiment, classification = get_openai_analysis(comment_text)

        new_comment = CalibrationComment(
            employee_id=employee_id,
            comment_type=comment_type,
            comment_text=comment_text,
            sentiment=sentiment,
            classification=classification
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('add_comment.html', employee=employee)

if __name__ == '__main__':
    app.run(debug=True)
