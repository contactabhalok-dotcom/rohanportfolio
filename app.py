from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database initialization
def init_db():
    try:
        # Ensure the database file exists and is valid
        if not os.path.exists('database.db'):
            open('database.db', 'w').close()
            
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Create projects table
        c.execute('''CREATE TABLE IF NOT EXISTS projects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      title TEXT NOT NULL,
                      description TEXT NOT NULL,
                      image_url TEXT,
                      demo_link TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Create skills table
        c.execute('''CREATE TABLE IF NOT EXISTS skills
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      percentage INTEGER NOT NULL,
                      category TEXT NOT NULL)''')
        
        # Create messages table
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      email TEXT NOT NULL,
                      subject TEXT NOT NULL,
                      message TEXT NOT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      read_status INTEGER DEFAULT 0)''')
        
        # Insert default skills
        default_skills = [
            ('HTML/CSS/JavaScript', 95, 'Frontend'),
            ('React/Vue.js', 85, 'Frontend'),
            ('Python/Flask', 90, 'Backend'),
            ('Node.js/Express', 80, 'Backend'),
            ('MySQL/PostgreSQL', 85, 'Database'),
            ('MongoDB', 75, 'Database'),
            ('AWS/Cloud Services', 70, 'Cloud'),
            ('Docker/Git', 80, 'DevOps')
        ]
        
        c.execute("SELECT COUNT(*) FROM skills")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO skills (name, percentage, category) VALUES (?, ?, ?)", default_skills)
        
        # Insert sample projects
        sample_projects = [
            ('E-Commerce Platform', 'A full-featured online store with shopping cart and payment integration', 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1170&q=80', 'https://github.com'),
            ('Task Management App', 'Productivity application for managing tasks and team collaboration', 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1139&q=80', 'https://github.com'),
            ('Analytics Dashboard', 'Data visualization dashboard with interactive charts and metrics', 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1170&q=80', 'https://github.com')
        ]
        
        c.execute("SELECT COUNT(*) FROM projects")
        if c.fetchone()[0] == 0:
            c.executemany("INSERT INTO projects (title, description, image_url, demo_link) VALUES (?, ?, ?, ?)", sample_projects)
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Try to delete and recreate the database file
        if os.path.exists('database.db'):
            os.remove('database.db')
        init_db()

init_db()

# Admin credentials
ADMIN_USERNAME = 'rohan'
ADMIN_PASSWORD = '8282913766r@A'

# Helper function to get database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route to serve images
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('images', filename)

# Routes
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        
        # Get projects
        projects = conn.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
        
        # Get skills grouped by category
        skills = conn.execute('SELECT * FROM skills ORDER BY category, percentage DESC').fetchall()
        
        conn.close()
        
        return render_template('index.html', projects=projects, skills=skills)
    except Exception as e:
        return f"Error loading page: {e}"

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (name, email, subject, message) VALUES (?, ?, ?, ?)',
                     (name, email, subject, message))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        
        # Get counts for dashboard
        projects_count = conn.execute('SELECT COUNT(*) FROM projects').fetchone()[0]
        skills_count = conn.execute('SELECT COUNT(*) FROM skills').fetchone()[0]
        messages_count = conn.execute('SELECT COUNT(*) FROM messages').fetchone()[0]
        unread_messages_count = conn.execute('SELECT COUNT(*) FROM messages WHERE read_status = 0').fetchone()[0]
        
        # Get recent messages
        recent_messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC LIMIT 5').fetchall()
        
        conn.close()
        
        return render_template('admin.html', 
                             projects_count=projects_count,
                             skills_count=skills_count,
                             messages_count=messages_count,
                             unread_messages_count=unread_messages_count,
                             recent_messages=recent_messages)
    except Exception as e:
        return f"Error loading admin dashboard: {e}"

# Projects Management
@app.route('/admin/projects')
def admin_projects():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        projects = conn.execute('SELECT * FROM projects ORDER BY created_at DESC').fetchall()
        conn.close()
        
        return render_template('admin_projects.html', projects=projects)
    except Exception as e:
        return f"Error loading projects: {e}"

@app.route('/admin/projects/add', methods=['POST'])
def add_project():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        title = request.form['title']
        description = request.form['description']
        image_url = request.form['image_url']
        demo_link = request.form['demo_link']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO projects (title, description, image_url, demo_link) VALUES (?, ?, ?, ?)',
                     (title, description, image_url, demo_link))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Project added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/projects/update/<int:project_id>', methods=['POST'])
def update_project(project_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        title = request.form['title']
        description = request.form['description']
        image_url = request.form['image_url']
        demo_link = request.form['demo_link']
        
        conn = get_db_connection()
        conn.execute('UPDATE projects SET title=?, description=?, image_url=?, demo_link=? WHERE id=?',
                     (title, description, image_url, demo_link, project_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Project updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/projects/delete/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM projects WHERE id=?', (project_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Project deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Skills Management
@app.route('/admin/skills')
def admin_skills():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        skills = conn.execute('SELECT * FROM skills ORDER BY category, percentage DESC').fetchall()
        conn.close()
        
        return render_template('admin_skills.html', skills=skills)
    except Exception as e:
        return f"Error loading skills: {e}"

@app.route('/admin/skills/add', methods=['POST'])
def add_skill():
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        name = request.form['name']
        percentage = int(request.form['percentage'])
        category = request.form['category']
        
        conn = get_db_connection()
        conn.execute('INSERT INTO skills (name, percentage, category) VALUES (?, ?, ?)',
                     (name, percentage, category))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Skill added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/skills/update/<int:skill_id>', methods=['POST'])
def update_skill(skill_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        name = request.form['name']
        percentage = int(request.form['percentage'])
        category = request.form['category']
        
        conn = get_db_connection()
        conn.execute('UPDATE skills SET name=?, percentage=?, category=? WHERE id=?',
                     (name, percentage, category, skill_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Skill updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/skills/delete/<int:skill_id>', methods=['POST'])
def delete_skill(skill_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM skills WHERE id=?', (skill_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Skill deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Messages Management
@app.route('/admin/messages')
def admin_messages():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        conn = get_db_connection()
        messages = conn.execute('SELECT * FROM messages ORDER BY created_at DESC').fetchall()
        conn.close()
        
        return render_template('admin_messages.html', messages=messages)
    except Exception as e:
        return f"Error loading messages: {e}"

@app.route('/admin/messages/read/<int:message_id>', methods=['POST'])
def mark_message_read(message_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        conn = get_db_connection()
        conn.execute('UPDATE messages SET read_status=1 WHERE id=?', (message_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message marked as read!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/messages/delete/<int:message_id>', methods=['POST'])
def delete_message(message_id):
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM messages WHERE id=?', (message_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)