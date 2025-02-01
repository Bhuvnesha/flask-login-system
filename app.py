from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import bcrypt

app = Flask(__name__)

# Secret key for session management
app.secret_key = '1234567890'

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Replace with your MySQL root password
app.config['MYSQL_DB'] = 'login_system'

mysql = MySQL(app)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if "loggedin" in session:
        return render_template('home.html')

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not email or not password:
            flash('Please fill out all fields!', 'error')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!', 'error')
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE username = %s OR email = %s', (username, email))
            account = cursor.fetchone()

            if account:
                flash('Username or email already exists!', 'error')
            else:
                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # Insert new user into the database
                cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
                mysql.connection.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if "loggedin" in session:
        return render_template('home.html')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()

        if account:
            # Verify the password
            if bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid username or password!', 'error')
        else:
            flash('Invalid username or password!', 'error')

    return render_template('login.html')

# Home route
@app.route('/home')
def home():
    if 'loggedin' in session:
        menus = get_menus()  # Fetch menus and submenus
        return render_template('home.html', username=session['username'], menus=menus)
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/settings/profile')
def profile():
    if 'loggedin' in session:
        return render_template('profile.html', username=session['username'])
    return redirect(url_for('login'))

# @app.route('/admin/menus')
# def manage_menus():
#     if 'loggedin' in session:
#         # fetch all menus and submenus
#         menus = get_menus()
#         return render_template('manage_menus.html', menus=menus)
#     return redirect(url_for('login'))

@app.route('/admin/menus', methods=['GET', 'POST'])
def manage_menus():
    if 'loggedin' in session:
        if request.method == 'POST':
            # Handle form submissions
            action = request.form.get('action')
            if action == 'add':
                # Add a new menu or submenu
                name = request.form['name']
                link = request.form['link']
                description = request.form['description']
                parent_id = request.form['parent_id'] if request.form['parent_id'] else None

                cursor = mysql.connection.cursor()
                cursor.execute(
                    'INSERT INTO menus (name, link, description, parent_id) VALUES (%s, %s, %s, %s)',
                    (name, link, description, parent_id)
                )
                mysql.connection.commit()
                flash('Menu added successfully!', 'success')

            elif action == 'edit':
                # Edit an existing menu or submenu
                menu_id = request.form['id']
                name = request.form['name']
                link = request.form['link']
                description = request.form['description']

                cursor = mysql.connection.cursor()
                cursor.execute(
                    'UPDATE menus SET name = %s, link = %s, description = %s WHERE id = %s',
                    (name, link, description, menu_id)
                )
                mysql.connection.commit()
                flash('Menu updated successfully!', 'success')

            elif action == 'delete':
                # Delete a menu or submenu
                menu_id = request.form['id']

                cursor = mysql.connection.cursor()
                cursor.execute('DELETE FROM menus WHERE id = %s', (menu_id,))
                mysql.connection.commit()
                flash('Menu deleted successfully!', 'success')

        # Fetch all menus and submenus
        menus = get_menus()
        return render_template('manage_menus.html', menus=menus)
    return redirect(url_for('login'))

def get_menus():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM menus WHERE parent_id IS NULL')  # Fetch top-level menus
    menus = cursor.fetchall()

    for menu in menus:
        cursor.execute('SELECT * FROM menus WHERE parent_id = %s', (menu['id'],))  # Fetch submenus
        menu['submenus'] = cursor.fetchall()

    return menus

# Run the app
if __name__ == '__main__':
    app.run(debug=True)