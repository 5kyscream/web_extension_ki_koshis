# app.py

from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
import sqlite3, io, os, bcrypt, pandas as pd, random
from functools import wraps
from backend import recommendInternship
import fitz  # PyMuPDF

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a-secure-default-secret-key-for-development")

DATABASE = 'pm_internship.sqlite'
CSV_FILE = 'pm_internship_data.csv'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: 
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("Rebuilding database schema...")
        
        cursor.execute("DROP TABLE IF EXISTS internships")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT NOT NULL, 
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL, 
                role TEXT NOT NULL CHECK(role IN ('student', 'company'))
            )""")
        
        cursor.execute("""
            CREATE TABLE internships (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                title TEXT NOT NULL, 
                description TEXT, 
                required_skills TEXT,
                company TEXT, 
                duration TEXT, 
                stipend INTEGER, 
                popularity INTEGER, 
                rating REAL, 
                company_prestige INTEGER,
                company_id INTEGER, 
                apply_url TEXT, 
                FOREIGN KEY (company_id) REFERENCES users (id)
            )""")
        
        print("Seeding initial users...")
        company_pass = bcrypt.hashpw(b"companypass", bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                      ("Ministry of Corporate Affairs", "mca@gov.in", company_pass, "company"))
        
        student_pass = bcrypt.hashpw(b"studentpass", bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                      ("Aditya Sharma", "aditya@student.com", student_pass, "student"))
        
        if os.path.exists(CSV_FILE):
            print(f"Loading data from {CSV_FILE} into database...")
            df = pd.read_csv(CSV_FILE)
            cursor.execute("SELECT id FROM users WHERE email = ?", ("mca@gov.in",))
            company_user = cursor.fetchone()
            company_id = company_user['id'] if company_user else 1
            df['company_id'] = company_id
            df.to_sql('internships', db, if_exists='append', index=False)
            print(f"Database populated with {len(df)} internships.")
        
        db.commit()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None: 
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def company_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.user['role'] != 'company': 
            return jsonify({'error': 'Company access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.user['role'] != 'student': 
            return jsonify({'error': 'Student access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    g.user = None
    if user_id:
        db = get_db()
        g.user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

# ===== ROUTES =====

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if g.user['role'] == 'student': 
        return redirect(url_for('student_dashboard'))
    elif g.user['role'] == 'company': 
        return redirect(url_for('company_dashboard'))
    return redirect(url_for('index'))

@app.route('/student-dashboard')
@student_required
def student_dashboard(): 
    return render_template('student_dashboard.html')

@app.route('/company-dashboard')
@company_required
def company_dashboard(): 
    return render_template('company_dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (data['email'],)).fetchone()
        
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            session.clear()
            session['user_id'] = user['id']
            return jsonify({'message': 'Login successful', 'role': user['role']})
        return jsonify({'error': 'Invalid email or password'}), 401
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db = get_db()
        
        try:
            db.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                      (data['name'], data['email'], password_hash, data['role']))
            db.commit()
            return jsonify({'message': 'Account created successfully'}), 201
        except sqlite3.IntegrityError: 
            return jsonify({'error': 'Email already exists'}), 409
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ===== STUDENT ROUTES =====

@app.route('/find-matches', methods=['POST'])
@student_required
def find_matches():
    if 'resume' not in request.files: 
        return jsonify({'error': 'No resume file provided'}), 400
    
    file = request.files['resume']
    if not file.filename.lower().endswith('.pdf'): 
        return jsonify({'error': 'Unsupported file type. Please upload a PDF file.'}), 400
    
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        resume_text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
    except Exception as e: 
        return jsonify({'error': f'Error processing PDF file: {e}'}), 500
    
    if not resume_text.strip(): 
        return jsonify({'error': 'Could not extract text from the PDF.'}), 400
    
    student = {"skills": resume_text}
    db = get_db()
    internships = [dict(row) for row in db.execute("SELECT * FROM internships").fetchall()]
    
    if not internships: 
        return jsonify({'error': 'No internship opportunities available.'}), 404
    
    recommendations = recommendInternship(student, internships, top_n=5)
    response = [{'score': round(s, 4), 'internship': i, 'explanation': e} for s, i, e in recommendations]
    
    return jsonify(response)

# ===== COMPANY ROUTES =====

@app.route('/add-internship', methods=['GET', 'POST'])
@company_required
def add_internship_page():
    if request.method == 'POST':
        data = request.get_json()
        db = get_db()
        
        # Generate random metrics for demonstration
        popularity = random.randint(40, 70)
        rating = round(random.uniform(3.8, 4.5), 1)
        prestige = random.randint(5, 8)
        
        db.execute("""
            INSERT INTO internships (title, description, required_skills, company, duration, stipend,
                                   company_id, apply_url, popularity, rating, company_prestige)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data['title'], data['description'], data['required_skills'], g.user['name'],
              data['duration'], data['stipend'], g.user['id'], data.get('apply_url', ''),
              popularity, rating, prestige))
        
        db.commit()
        return jsonify({'message': 'Internship added successfully'}), 201
    
    return render_template('add_internship.html')

@app.route('/api/company/internships')
@company_required
def get_company_internships():
    db = get_db()
    internships = db.execute("SELECT * FROM internships WHERE company_id = ? ORDER BY id DESC", 
                           (g.user['id'],)).fetchall()
    return jsonify([dict(row) for row in internships])

@app.route('/api/internship/delete/<int:id>', methods=['DELETE'])
@company_required
def delete_internship(id):
    db = get_db()
    internship = db.execute("SELECT id FROM internships WHERE id = ? AND company_id = ?", 
                          (id, g.user['id'])).fetchone()
    
    if internship:
        db.execute("DELETE FROM internships WHERE id = ?", (id,))
        db.commit()
        return jsonify({'message': 'Internship deleted successfully'}), 200
    
    return jsonify({'error': 'Internship not found or unauthorized'}), 404

# ===== ADDITIONAL ROUTES =====

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/results')
def results_page():
    return render_template('results.html')

@app.route('/allocation-results')
def allocation_results():
    return render_template('allocation_results.html')

@app.route('/edit-internship/<int:id>')
@company_required
def edit_internship(id):
    db = get_db()
    internship = db.execute("SELECT * FROM internships WHERE id = ? AND company_id = ?", 
                          (id, g.user['id'])).fetchone()
    
    if not internship:
        return redirect(url_for('company_dashboard'))
    
    return render_template('edit_internship.html', internship=dict(internship))

@app.route('/api/internship/update/<int:id>', methods=['PUT'])
@company_required
def update_internship(id):
    data = request.get_json()
    db = get_db()
    
    internship = db.execute("SELECT id FROM internships WHERE id = ? AND company_id = ?", 
                          (id, g.user['id'])).fetchone()
    
    if not internship:
        return jsonify({'error': 'Internship not found or unauthorized'}), 404
    
    db.execute("""
        UPDATE internships 
        SET title = ?, description = ?, required_skills = ?, duration = ?, stipend = ?, apply_url = ?
        WHERE id = ?
    """, (data['title'], data['description'], data['required_skills'], 
          data['duration'], data['stipend'], data.get('apply_url', ''), id))
    
    db.commit()
    return jsonify({'message': 'Internship updated successfully'})

@app.route('/api/stats')
@company_required
def get_stats():
    db = get_db()
    internships = db.execute("SELECT * FROM internships WHERE company_id = ?", 
                           (g.user['id'],)).fetchall()
    
    internships_list = [dict(row) for row in internships]
    total_internships = len(internships_list)
    
    if total_internships > 0:
        avg_rating = sum(i.get('rating', 0) for i in internships_list) / total_internships
        total_stipend = sum(i.get('stipend', 0) for i in internships_list)
    else:
        avg_rating = 0
        total_stipend = 0
    
    return jsonify({
        'total_internships': total_internships,
        'avg_rating': round(avg_rating, 1),
        'total_stipend': total_stipend
    })

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return render_template('index.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
