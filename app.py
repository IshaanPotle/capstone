from flask import Flask, render_template, request, Response, session, redirect, url_for
import time
import cohere
import mysql.connector

app = Flask(__name__, static_url_path='/static')
co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

# MySQL configuration
db_config = {
    'host': 'localhost',     # Change this to your MySQL server address
    'user': 'localhost',      # Change this to your MySQL username
    'password': '',  # Change this to your MySQL password
    'database': 'capstone'  # Change this to the name of your MySQL database
}

# Function to establish MySQL connection
def get_mysql_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Exception as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/')
def index():
    if 'email' in session:
        # User is authenticated, get the email from session
        email = session['email']
        # Pass the email to the template
        return render_template('index.php', email=email)
    else:
        # User is not authenticated, redirect to login page
        return redirect(url_for('login.php'))

@app.route('/topics_listing')
def topics_listing():
    return render_template('topics_listing.php')

@app.route('/topics-detail')
def topics_detail():
    return render_template('topics-detail.php')

@app.route('/contact')
def contact():
    return render_template('contact.php')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the database to check if the user exists and the password is correct
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM auth WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and user['password'] == password:
            # User authenticated, store user's email in session
            session['email'] = email
            print("User logged in successfully")  # Add print statement for debugging
            return redirect(url_for('index'))  # Redirect to a protected page after login
        else:
            # Invalid credentials, show error message
            error = "Invalid email or password. Please try again."
            print("Invalid email or password")  # Add print statement for debugging
            return render_template('login.php', error=error)
    else:
        return render_template('login.php')


@app.route('/register')
def register():
    return render_template('register.php')

@app.route('/conn')
def conn():
    return render_template('conn.php')

@app.route('/generate', methods=['POST'])
def generate():
    keyword = request.form['keyword']
    return Response(generate_with_cohere(keyword), content_type='text/event-stream')

def generate_with_cohere(keyword):
    for event in co.chat(f"Explain {keyword} to me ", stream=True):
        if event.event_type == cohere.responses.chat.StreamEvent.TEXT_GENERATION:
            generated_text = f"{event.text}"  # Wrap each line in a <p> tag for better formatting
            yield generated_text

        elif event.event_type == cohere.responses.chat.StreamEvent.STREAM_END:
            yield f""


if __name__ == '__main__':
    connection = get_mysql_connection()
    if connection:
        app.secret_key = 'your_secret_key'
        # If connection is successful, run the Flask application
        app.run(debug=True)
    else:
        # If connection fails, print an error message
        print("Failed to establish MySQL connection. Exiting.")
