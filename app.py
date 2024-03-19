from flask import Flask, render_template, request, Response, session, redirect, url_for
import time
import cohere
import mysql.connector
import json

app = Flask(__name__, static_url_path='/static')
co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

# Global variables
subjects=None
answerList = []
questionList = []

# MySQL configuration
db_config = {
    'host': 'localhost',     # Change this to your MySQL server address
    'user': 'root',      # Change this to your MySQL username
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
        return render_template('index.html', email=email)
    else:
        # User is not authenticated, redirect to login page
        return redirect(url_for('login'))

@app.route('/subjects')
def subjects():
    # Connect to MySQL database
    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        # Query to retrieve subject names
        cursor.execute("SELECT DISTINCT Subject FROM subject")
        subjects = cursor.fetchall()
        cursor.close()
        connection.close()
        # Pass the subjects data to the template
        return render_template('subjects.html', subjects=subjects)

@app.route('/subtopics', methods=['GET','POST'])
def subtopics():

    selected_chapter = None
    if request.method == 'POST':
        selected_chapter = request.form['subject']
        print(selected_chapter)
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            # Query to retrieve subtopics for the selected subject
            cursor.execute("SELECT Subtopics FROM subject WHERE Chapter = %s", (selected_chapter,))
            subtopics = cursor.fetchall()
            print("Subtopics fetched from the database:", subtopics)  # Add this line to check the data structure
            cursor.close()
            connection.close()
            # Pass the subtopics data to the template
            return render_template('subtopics.html', subtopics=subtopics)
        else:
            return "Failed to establish MySQL connection. Please check your database settings."

    
@app.route('/chapters', methods=['GET', 'POST'])
def chapters():
    selected_subject = None
    if request.method == 'POST':
        selected_subject = request.form['Chapter']
        print(selected_subject)

    try:
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Query to retrieve chapters for the selected subject
            cursor.execute("SELECT Chapter FROM subject WHERE Subject = %s", (selected_subject,))
            chapters = cursor.fetchall()
            
            # Close cursor and connection
            cursor.close()
            connection.close()
            
            if chapters:
                # Pass the chapters data to the template
                return render_template('chapters.html', chapters=chapters)
            else:
                return "No chapters found for selected subject: {}".format(selected_subject)
    except Exception as e:
        return "An error occurred: {}".format(str(e))
    

@app.route('/textualcontent', methods=['GET', 'POST'])
def textualcontent():
    if request.method == 'POST':
        subtopic = request.form['subject']
        print(request.form)

        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Construct and print the query for debugging
            query = "SELECT TextualContent FROM subject WHERE Subtopics = %s"
            
            # Execute the query with the subtopic value
            cursor.execute(query, (subtopic,))
            
            # Fetch the result
            textual_content = cursor.fetchone()

            print(textual_content)
            
            cursor.close()
            connection.close()

            # If textual content is found, render the template with it
            if textual_content:
                return render_template('textualcontent.html', textual_content=textual_content['TextualContent'])  # Access 'TextualContent' key
            else:
                return "No textual content found for this subtopic: " + subtopic  # Return the subtopic for debugging
        else:
            return "Failed to establish MySQL connection. Please check your database settings."

@app.route('/videocontent', methods=['GET', 'POST'])
def videocontent():
    if request.method == 'POST':
        subtopic = request.form['subject']
        
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Construct the query to fetch video content
            query = "SELECT Video FROM subject WHERE Subtopics = %s"
            
            # Execute the query with the subtopic value
            cursor.execute(query, (subtopic,))
            
            # Fetch the result
            video_content = cursor.fetchone()
            
            cursor.close()
            connection.close()

            # If video content is found, construct the iframe URL and render the template with it
            if video_content:
                # Extract the video ID from the URL
                video_id = video_content['Video'].split('/')[-1]
                iframe_url = f"https://www.youtube.com/embed/{video_id}"
                return render_template('videocontent.html', iframe_url=iframe_url)
            else:
                return "No video content found for this subtopic: " + subtopic  # Return the subtopic for debugging
        else:
            return "Failed to establish MySQL connection. Please check your database settings."



@app.route('/topics_listing')
def topics_listing():
    return render_template('topics_listing.html')

@app.route('/topics-detail')
def topics_detail():
    return render_template('topics-detail.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/mcq')
def mcq():
    global subjects
    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        # Query to retrieve subject names
        cursor.execute("SELECT Subject FROM subject")
        subjects1 = cursor.fetchall()

        subjects = subjects1
        cursor.close()
        connection.close()
        # Pass the subjects data to the template
        return render_template('mcq.html', subjects=subjects1)
    

@app.route('/takemcq', methods=['POST'])
def subject_detail():
    # Get the subject name from the form submission
    subject_name = request.form['subject']

    # Connect to MySQL database
    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        # Query to retrieve subtopics for the selected subject
        cursor.execute("SELECT Subtopics FROM Subject WHERE Subject = %s", (subject_name,))
        subtopics = cursor.fetchall()
        cursor.close()
        connection.close()

        # Extract subtopics strings from the result
        subtopic_list = [subtopic['Subtopics'] for subtopic in subtopics]

        # Pass the subtopics data to the API
        api_response = generate_pre_mcq(subtopic_list)

        # Convert api_response to JSON string
        # api_response_str = str(api_response)
        print(type(api_response))
        global answerList
        answerList.clear()
        # Saving the answers in the list
        for i in api_response['questions']:
            answerList.append(i['answer'])

        global questionList
        questionList.clear()
        # Saving the questions in the list
        for i in api_response['questions']:
            print(i['question'])
            questionList.append(i['question'])
        # api_response_json = json.loads(api_response)
        # print(type(api_response))
        # print(type(api_response_json))

        # print(type(api_response_json))
        # print(api_response_json['questions'])
        return render_template('premcq.html', api_response=api_response ,notify = False)

    else:
        return "Failed to establish MySQL connection. Please check your database settings."



@app.route('/checkAns', methods=['POST'])
def ans():
    answerSelected = []
    for i in questionList:
        answerSelected.append(request.form[i])

    global answerList
    # Count the number of matched items
    matched_items = len(set(answerSelected) & set(answerList))
    print(matched_items)

    # Update the score of the user for the selected topic
    cursor = connection.cursor(dictionary=True)

    UserID = session['UserId']  # Assuming session['UserId'] contains the user's ID
    subject = subjects[0]['Subject']
    score = matched_items
    print(UserID, subject, score)


    cursor.execute('INSERT INTO Scores (UserId, Subject, SubjectScore, Topic, TopicScore) VALUES (%s, %s, %s, %s, %s)',(UserID, subject, score, '-', 0))

    connection.commit()

    score = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('premcq.html', notify = True, matched_items = matched_items)

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
            session['UserId'] = user['id']
            print("User logged in successfully")  # Add print statement for debugging
            return redirect(url_for('index'))  # Redirect to a protected page after login
        else:
            # Invalid credentials, show error message
            error = "Invalid email or password. Please try again."
            print("Invalid email or password")  # Add print statement for debugging
            return render_template('login.html', error=error)
    else:
        return render_template('login.html')

    
def generate_pre_mcq(keyword):
    response = co.generate(
        prompt=f"Strictly Only Give total 10 MCQs on the following topics {keyword} in JSON Format format. Your response should not contain anything else",
    )

    # Extracting JSON from response text
    json_text = response.text.strip()
    json_start_index = json_text.find("{")
    json_end_index = json_text.rfind("}")
    if json_start_index != -1 and json_end_index != -1:
        return json_text[json_start_index:json_end_index+1]
    else:
        print("No JSON content found in the response.")
        return None


@app.route('/logout',methods=['GET','POST'])
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Determine the role based on the email suffix
        if email.endswith('@nmims.edu'):
            role = 'Teacher'
        else:
            role = 'Student'

        # Insert the new user into the database
        conn = get_mysql_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO auth (email, password, role) VALUES (%s, %s, %s)', (email, password, role))
            conn.commit()
            message = 'User registered successfully'
        except mysql.connector.Error as e:
            message = f'Error: {e}'
        finally:
            conn.close()

        # Redirect to the login page upon successful registration
        return redirect(url_for('login'))

    return render_template('register.html', message=message)


@app.route('/generate', methods=['POST'])
def generate():
    keyword = request.form['keyword']
    return Response(generate_with_cohere(keyword), content_type='text/event-stream')

def fix_json_syntax(json_str):
    # Find the index of the error
    error_index = json_str.find('}')

    # Insert a comma at the error index
    fixed_json = json_str[:error_index] + ',' + json_str[error_index:]
    return fixed_json

def generate_pre_mcq(keyword):
    response = co.generate(
    prompt = f"Strictly Only Give total 10 MCQs on the following topics {keyword} in JSON Format format, the answer should be one of the options example: {{\"questions\": [{{\"question\": \"What is the capital of France?\",\"options\": [\"Paris\",\"London\",\"Berlin\",\"Rome\"],\"answer\": \"Paris\"}}]}} ensure that the json format you give is correct as well as there is no extra data error in JSON."
    )
    start_index = response.generations[0].text.find('{')
    end_index = response.generations[0].text.rfind('}')

    if start_index != -1 and end_index != -1:
        # Extract the substring between the first '{' and the last '}'
        json_text = response.generations[0].text[start_index:end_index+1]
        print("json_text",type(json_text))
        print("json_text",json_text)
        json_text = json.loads(json_text)
        print("json_text",type(json_text))
        return json_text
    else:
        print("No JSON content found in the response.")



def generate_with_cohere(keyword):
    for event in co.chat(f"Explain {keyword} in 1000 words to me and give output in HTML format", stream=True):
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
