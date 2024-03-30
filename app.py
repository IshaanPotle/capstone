from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service  #
import re
from os import name
from flask import Flask, render_template, request, Response, session, redirect, url_for, jsonify
import time
import cohere
import mysql.connector
import json
from bs4 import BeautifulSoup
import numpy as np
import urllib
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from urllib.parse import urljoin
from adaptive_learning import AdaptiveLearningModel

app = Flask(__name__, static_url_path='/static')
co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

# Global variables
subjects = None
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
        name = session.get('name') 
        # Pass the email to the template
        return render_template('index.html', email=email, name=name)
    else:
        # User is not authenticated, redirect to login page
        return redirect(url_for('login'))

# Display Name 
@app.context_processor
def inject_name():
    name = session.get('name')
    return dict(name=name)

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
    role = session.get('role')
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
                return render_template('textualcontent.html', textual_content=textual_content['TextualContent'], subtopic=subtopic, role=role,textual_content_id=id ,is_content_approved=is_content_approved)  # Access 'TextualContent' key
            else:
                return "No textual content found for this subtopic: " + subtopic  # Return the subtopic for debugging
        else:
            return "Failed to establish MySQL connection. Please check your database settings."
        

def get_transcript(video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            formatted_transcript = []
            for line in transcript:
                start = line['start']
                end = line['start'] + line['duration']
                text = line['text']
                formatted_transcript.append({'start': start, 'end': end, 'text': text})
            return formatted_transcript
        except Exception as e:
            print("Error:", e)
            return None
def extract_video_id(iframe_code):
            match = re.search(r'src=".*?youtube\.com/embed/([A-Za-z0-9_-]+)', iframe_code)
            if match:
                return match.group(1)
            else:
                return None

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
                video_id = extract_video_id(video_content['Video'])
                iframe_url = f"https://www.youtube.com/embed/{video_id}"
                transcript = get_transcript(video_id)

                return render_template('videocontent.html', iframe_url=iframe_url)
            else:
                return "No video content found for this subtopic: " + subtopic  # Return the subtopic for debugging
        else:
            return "Failed to establish MySQL connection. Please check your database settings."
    else:
        return render_template('videocontent.html') 


@app.route('/progress_report')
def progress_report():
    return render_template('progress_report.html')

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


# @app.route('/mcq')
# def mcq():
#     global subjects
#     connection = get_mysql_connection()
#     if connection:
#         cursor = connection.cursor(dictionary=True)
#         # Query to retrieve subject names
#         cursor.execute("SELECT Subject FROM subject")
#         subjects1 = cursor.fetchall()

#         subjects = subjects1
#         cursor.close()
#         connection.close()

#         # Inject user level into template context
#         user_level = inject_user_level()['user_level']

#         # Pass the subjects data and user level to the templates
#         return render_template('mcq.html', subjects=subjects1, user_level=user_level)


# WORKING BUT NOT DISPLAYING LEVEL CORRECTLY 
# @app.context_processor
# def inject_user_level():
#     email = session.get('email')  # Retrieve email from session
#     user_levels = {}  # Dictionary to store user levels for each subject

#     if email:
#         connection = get_mysql_connection()
#         if connection:
#             try:
#                 cursor = connection.cursor(dictionary=True)

#                 # Query to retrieve the user's ID based on their email
#                 query = "SELECT id FROM auth WHERE email = %s"
#                 cursor.execute(query, (email,))
#                 user_data = cursor.fetchone()

#                 if user_data:
#                     user_id = user_data['id']

#                     # Query to retrieve subject names
#                     cursor.execute("SELECT Subject FROM subject")
#                     subjects = cursor.fetchall()

#                     for subject in subjects:
#                         # Query to retrieve the user's level for each subject
#                         query = "SELECT Level FROM scores WHERE UserId = %s AND Subject = %s"
#                         cursor.execute(query, (user_id, subject['Subject']))
#                         level_data = cursor.fetchone()

#                         print("Subject:", subject['Subject'])  # Debug print to check the subject
#                         print("Level Data:", level_data) 

#                         if level_data:
#                             user_levels[subject['Subject']] = level_data['Level']  # Use 'Level' instead of 'level'
#                         else:
#                             user_levels[subject['Subject']] = "No level found"
                        
#                         cursor.fetchall()
#                 else:
#                     user_levels["No user found"] = None 

#             except mysql.connector.Error as e:
#                 print(f"Error executing MySQL query: {e}")
#                 user_levels["Error fetching user levels"] = None

#             finally:
#                 cursor.fetchall()  # Ensure all results are consumed
#                 cursor.close()
#                 connection.close()

#     return {'user_levels': user_levels}


# @app.route('/mcq')
# def mcq():
#     global subjects
#     connection = get_mysql_connection()
#     if connection:
#         cursor = connection.cursor(dictionary=True)
#         # Query to retrieve subject names
#         cursor.execute("SELECT Subject FROM subject")
#         subjects = cursor.fetchall()

#         cursor.close()
#         connection.close()

#         # Inject user levels into template context
#         user_levels = inject_user_level()['user_levels']

#         # Pass the subjects data and user levels to the template
#         return render_template('mcq.html', subjects=subjects, user_levels=user_levels)

# -----------------------------------------------------

@app.route('/mcq')
def mcq():
    global subjects
    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        # Query to retrieve subject names
        cursor.execute("SELECT Subject FROM subject")
        subjects = cursor.fetchall()

        cursor.close()
        connection.close()

        # Pass the subjects data to the template
        return render_template('mcq.html', subjects=subjects)


@app.context_processor
def inject_user_level():
    email = session.get('email')  # Retrieve email from session
    user_levels = {}  # Dictionary to store user levels for each subject

    if email:
        connection = get_mysql_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Query to retrieve the user's ID based on their email
                query = "SELECT id FROM auth WHERE email = %s"
                cursor.execute(query, (email,))
                user_data = cursor.fetchone()

                if user_data:
                    user_id = user_data['id']

                    # Query to retrieve subject names
                    cursor.execute("SELECT Subject FROM subject")
                    subjects = cursor.fetchall()

                    for subject in subjects:
                        # Query to retrieve the user's level for each subject
                        query = "SELECT Level FROM scores WHERE UserId = %s AND Subject = %s"
                        cursor.execute(query, (user_id, subject['Subject']))
                        level_data = cursor.fetchone()

                        if level_data:
                            user_levels[subject['Subject']] = level_data['Level']
                        else:
                            user_levels[subject['Subject']] = "Not yet attempted"
                else:
                    user_levels["No user found"] = None

            except mysql.connector.Error as e:
                print(f"Error executing MySQL query: {e}")
                user_levels["Error fetching user levels"] = None

            finally:
                cursor.fetchall()  # Ensure all results are consumed
                cursor.close()
                connection.close()

    return {'user_levels': user_levels}

# ------------------------------------------------

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
        # cursor.close()
        # connection.close()
      
        if user and user['password'] == password:
            # User authenticated, store user's email in session
            session['email'] = email
            session['UserId'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for('index'))  # Redirect to a protected page after login
        else:
            # Invalid credentials, show error message
            error = "Invalid email or password. Please try again."
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

def scrape_khan_academy_articles(topic):
    base_url = "https://www.khanacademy.org/search?search_again=1&page_search_query="
    content_kinds = "&content_kinds=Article"
    search_url = base_url + topic.replace(" ", "%20") + content_kinds

    # Use a headless browser to render the JavaScript content
    driver = webdriver.Chrome()
    driver.get(search_url)

    try:
        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'div')))
        # Get the page source after JavaScript has loaded
        page_source = driver.page_source
    finally:
        driver.quit()

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')
    articles = []

    search_results = soup.find_all('div', class_="_16owliz9")  # Finding each search result item

    # Counter for limiting articles to 5
    count = 0

    for index, result in enumerate(search_results):
        # Check if already scraped 5 articles
        if count >= 5:
            break

        # Your code to extract information from each search result
        a_tag = result.find('a', class_="_xne4a47")  # Find the anchor tag
        if a_tag:
            href = a_tag['href']  # Extract the href attribute

            # Find the title within the additional div
            title_div = result.find('div', class_="_pxfwtyj")
            title = title_div.text.strip() if title_div else "Title not available"  # Extract the title or handle missing title

            # Find the description within the span
            description_span = result.find('span', class_="_w68pn83")
            description = description_span.text.strip() if description_span else ""  # Extract the description or handle missing description

            articles.append({'result_id': index, 'title': title, 'description': description, 'href': href})

            count += 1  # Increment the counter for each scraped article

    return articles

def scrape_article_content(url):
    # Fetch the article page content using requests
    response = requests.get(url)
    if response.status_code == 200:
        page_source = response.text
    else:
        print("Failed to fetch article content:", response.status_code)
        return []

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all div elements with the class "paragraph"
    paragraph_divs = soup.find_all('div', class_='paragraph')

    # Extract the text content, images, and nested h2 tags from each paragraph div
    article_content = []
    seen_texts = set()  # Store seen texts to avoid duplicates
    for div in paragraph_divs:
        # Find images within the div
        img_tags = div.find_all('img')
        for img_tag in img_tags:
            img_url = img_tag['src']
            credit = img_tag.find_next('em')
            credit_text = credit.get_text(strip=True) if credit else None
            article_content.append({'type': 'image', 'url': img_url, 'credit': credit_text})
        
        # Find all h2 tags within the div
        h2_tags = div.find_all('h2')
        for h2_tag in h2_tags:
            # Extract the text content of the h2 tag
            h2_content = h2_tag.text.strip()
            if h2_content not in seen_texts:
                article_content.append({'type': 'h2', 'content': h2_content, 'bold': True})  # Mark as bold
                seen_texts.add(h2_content)

            # Check if there is no text immediately following the h2 tag
            next_element = h2_tag.find_next_sibling()
            if not next_element or not next_element.get_text(strip=True):
                article_content.append({'type': 'text', 'content': ''})  # Add an empty text entry

        # Extract the text content of the div
        paragraph_text = div.get_text(strip=True)
        if paragraph_text and paragraph_text not in seen_texts:
            article_content.append({'type': 'text', 'content': paragraph_text})
            seen_texts.add(paragraph_text)

    return article_content

@app.route('/articles')
def show_article_content():
    result_id = request.args.get('id')
    topic = request.args.get('topic')  # Retrieve topic from request parameters
    base_url = "https://www.khanacademy.org"  # Base URL of the Khan Academy website
    
    print("result_id:", result_id)
    print("topic:", topic)
    
    # Check if result_id and topic are not None
    if result_id is not None and result_id.isdigit() and topic is not None:
        result_id = int(result_id)
        articles = scrape_khan_academy_articles(topic)
        print("articles:", articles)
        if 0 <= result_id < len(articles):
            article_href = articles[result_id]['href']
            print("This is the href", article_href)
            
            # Construct the absolute URL
            url = urllib.parse.urljoin(base_url, article_href)
            print("This is the full URL", url)
            
            # Scrape article content
            article_content = scrape_article_content(url)
            
            # Manually add index to each item in article content
            article_content_with_index = [(index, item) for index, item in zip(range(len(article_content)), article_content)]
            
            # Print out image URLs for debugging
            for index, item in article_content_with_index:
                if item['type'] == 'image':
                    print("Image URL:", item['url'])

            print("topic:", topic)
            print("articles:", articles)

            return render_template('articles.html', article_content=article_content_with_index)  # Split article content into paragraphs
    return "Article not found"

@app.route('/search', methods=['GET'])
def search():
    topic = request.args.get('topic')
    if topic:
        articles = scrape_khan_academy_articles(topic)
        return render_template('search_results.html', results=articles, topic=topic)  # Pass topic to template
    else:
        return "No topic provided"


# -------------------------------
# FETCHING THE LEVEL 

# @app.context_processor
# def inject_user_level():
#     def inner(subjects):
#         connection = get_mysql_connection()
#         if connection:
#             cursor = connection.cursor(dictionary=True)
#             level_dict = {}

#             for subject in subjects:
#                 query = "SELECT Level FROM scores WHERE UserId = %s AND Subject = %s"
#                 cursor.execute(query, (session.get('UserId'), subject['Subject']))
#                 result = cursor.fetchone()
#                 level_dict[subject['Subject']] = result['Level'] if result else "Error fetching user level"

#             cursor.close()
#             connection.close()
#             return {'user_levels': level_dict}
    
#     return inner




#-------------------------------------------------------
# @app.context_processor
# def inject_user_level():
#     email = session.get('email')  # Retrieve email from session
#     level = None  # Default level is None

#     print("User Email:", email)  # Debug print to check the email value

#     if email:
#         connection = get_mysql_connection()
#         if connection:
#             try:
#                 cursor = connection.cursor(dictionary=True)

#                 # Query to retrieve the user's ID based on their email
#                 query = "SELECT id FROM auth WHERE email = %s"
#                 cursor.execute(query, (email,))
#                 user_data = cursor.fetchone()

#                 print("User Data:", user_data)  # Debug print to check the user data

#                 if user_data:
#                     user_id = user_data['id']  # Fetch the user's ID from the result
#                     cursor.fetchone()
#                     # Query to retrieve the user's level based on their ID
#                     query = "SELECT level FROM scores WHERE UserId = %s"
#                     cursor.execute(query, (user_id,))
#                     level_data = cursor.fetchone()

#                     print("Level Data:", level_data)  # Debug print to check the level data

#                     if level_data:
#                         level = level_data['level']  # Fetch the level from the result
#                     else:
#                         level = "No level found"
#                 else:
#                     level = "No user found"

#             except mysql.connector.Error as e:
#                 print(f"Error executing MySQL query: {e}")
#                 level = "Error fetching user level"

#             finally:
#                 cursor.fetchall()  # Ensure all results are consumed before closing the cursor
#                 cursor.close()
#                 connection.close()

#     print("User Level:", level)  # Debug print to check the level value
#     return {'user_level': level}

#----------------------------------------


# ADAPTIVE LEARNING 

# model = AdaptiveLearningModel()

# @app.route('/update_score', methods=['POST'])
# def update_score():
#     data = request.get_json()
#     user_id = data['user_id']
#     subject = data['subject']
#     topic = data['topic']
#     mcq_score = data['mcq_score']
#     action = data['action']
    
#     model.update_score(user_id, subject, topic, mcq_score, action)
    
#     return jsonify({'message': 'Score updated successfully'})
# EXISTING CODE

# Define the Q-table
# q_table = np.zeros((11, 3))  # Q-table for 11 MCQ scores (0 to 10) and 3 levels (1, 2, 3)

# # Define the learning parameters
# learning_rate = 0.1
# discount_factor = 0.9
# exploration_rate = 0.1

# Route to handle defining level requests
# @app.route('/define_level', methods=['POST'])
# def define_level():
#     data = request.json
#     mcq_score = data['mcq_score']
    
#     # Choose an action based on epsilon-greedy policy
#     if np.random.uniform(0, 1) < exploration_rate:
#         action = np.random.choice(3) 
#     else:
#         action = np.argmax(q_table[mcq_score])  
    
#     level = action + 1  
    
#     return jsonify({"level": level})

# # Route to handle updating Q-table
# @app.route('/update_q_table', methods=['POST'])
# def update_q_table():
#     data = request.json
#     mcq_score = data['mcq_score']
#     level = data['level']
#     reward = data['reward']
    
#     # Update Q-table based on Q-learning update rule
#     old_value = q_table[mcq_score, level - 1]  
#     max_future_value = np.max(q_table[mcq_score + 1])
#     new_value = old_value + learning_rate * (reward + discount_factor * max_future_value - old_value)
#     q_table[mcq_score, level - 1] = new_value  
    
#     return jsonify({"message": "Q-table updated successfully"})

@app.route('/logout',methods=['GET','POST'])
def logout():
    # Clear the session data
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if '@' not in email:
            error = "Email address must contain '@'."
            return render_template('register.html', error=error)

        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM auth WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # User already exists, show error message
            error = "User already exists. Please login instead."
            return render_template('login.html', error=error)
        
        # Determine the role based on the email suffix
        if email.endswith('@nmims.edu'):
            role = 'Teacher'
        else:
            role = 'Student'

        # Insert the new user into the database
        conn = get_mysql_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO auth (name, email, password, role) VALUES (%s, %s, %s, %s)', (name, email, password, role))
            conn.commit()
            message = 'User registered successfully'
        except mysql.connector.Error as e:
            message = f'Error: {e}'
        finally:
            conn.close()

        session['role'] = role
        # Redirect to the login page upon successful registration
        return redirect(url_for('login'))    

    return render_template('register.html', message=message)

def update_reading_status(student_id, textual_content_id, read_status):
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()

        # Update the reading status in the database
        cursor.execute("UPDATE student_reading_status SET read_status = %s WHERE student_id = %s AND textual_content_id = %s",
                       (read_status, student_id, textual_content_id))
        connection.commit()

        # Close cursor and connection
        cursor.close()
        connection.close()

        return True  # Success
    except mysql.connector.Error as e:
        print(f"Error updating reading status: {e}")
        return False  # Failure

# Route to handle submission of reading status by students
@app.route('/submit_reading_status', methods=['POST'])
def submit_reading_status():
    if request.method == 'POST':
        student_id = request.form['student_id']
        textual_content_id = request.form['textual_content_id']
        read_status = request.form['read_status']
        # Update database with student's reading status
        success = update_reading_status(student_id, textual_content_id, read_status)
        if success:
            return "Reading status submitted successfully"
        else:
            return "Failed to submit reading status", 500  # Internal server error

def update_approval_status(textual_content_id, approved=True):
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE student_reading_status SET approval_status = %s WHERE textual_content_id = %s", (int(approved), textual_content_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error updating approval status:", e)
        return False

@app.route('/approve_content', methods=['POST'])
def approve_content():
    if request.method == 'POST':
        textual_content_id = request.form.get('textual_content_id')

        if not textual_content_id:
            return "Textual Content ID is missing", 400  # Bad request status code
        
        try:
            # Check if the content is already approved
            if is_content_approved(textual_content_id):
                return "Content is already approved"

            # If the content is not already approved, proceed with approval
            success = update_approval_status(textual_content_id, approved=True)
            if success:
                return "Content approved successfully"
            else:
                return "Failed to approve content", 500  # Internal server error status code
        
        except Exception as e:
            return f"An error occurred: {str(e)}", 500  # Internal server error status code

def is_content_approved(textual_content_id):
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT approval_status FROM student_reading_status WHERE textual_content_id = %s", (textual_content_id,))
        result = cursor.fetchone()
        if result and result[0] == 1:  # Assuming 'approval_status' is a boolean column where 1 represents approval
            print("It is approved")
            return True
        else:
            return False
    except Exception as e:
        print("Error checking approval status:", e)
        return False


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
