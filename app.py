import email
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service  #
import re
from os import name
from flask import Flask, render_template, request, Response, session, redirect, url_for, jsonify
import pymysql
import pymysql.cursors
import datetime
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
from pymysql import Error

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

def get_user_info():
    email = session.get('email')
    name = session.get('name')
    role = session.get('role')
    return {'email': email, 'name': name, 'role': role}

@app.route('/')
def index():
    if 'email' in session:
        return render_template('index.html', user=get_user_info())
    else:
        # User is not authenticated, redirect to login page
        return redirect(url_for('login'))
    
@app.context_processor
def inject_email():
    email = session.get('email')
    return dict(email=email)


@app.context_processor
def inject_user_info():
    # Retrieve user name and role from session
    name = session.get('name')
    role = session.get('role')

    # Return the user's name and role to be injected into the context
    return {'user_name': name, 'user_role': role}
# --------------------------------------------------
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
        return render_template('subjects.html',  user=get_user_info(),subjects=subjects)

@app.route('/subtopics', methods=['GET','POST'])
def subtopics():
    email = session.get('email')
    name = session.get('name')
    selected_subject = session.get('selected_subject')  
    text_id = session.get('text_id')
    video_id = session.get('video_id')
    selected_chapter = None
    if request.method == 'POST':
        selected_chapter = request.form['subject']
        print(email)
        print(selected_chapter)
        print(selected_subject)
        subtopics_data = []
        read_status_list = []
        watch_status_list = []
        read_status = 0
        watch_status = 0
        read_status_dt = {}
        watch_status_dt = {}
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                # Fetching subtopics along with subject details including SubjectLevel
                if email and selected_subject:
                    cursor.execute("SELECT Subtopics FROM subject WHERE Chapter = %s", (selected_chapter,))
                    subtopics = cursor.fetchall()
                    cursor.close()

                    # Fetching SubjectLevel from the score table
                    cursor = connection.cursor(dictionary=True)  # Reopen cursor
                    cursor.execute("SELECT DISTINCT SubjectLevel FROM score WHERE email = %s AND Subject = %s", (email, selected_subject))
                    subject_level_result = cursor.fetchone()
                    subject_level_str = subject_level_result['SubjectLevel'] if subject_level_result and 'SubjectLevel' in subject_level_result else None
                    subject_level = int(subject_level_str) if subject_level_str is not None else None
                    print(subject_level)
                    cursor.close()  

                    cursor = connection.cursor(dictionary=True)
                    # cursor.execute("""SELECT sub.Subtopics, s.read_status, s.watch_status FROM status AS s INNER JOIN subject AS sub ON s.text_id = sub.id WHERE s.student_name = %s """, (name,))
                    cursor = connection.cursor(dictionary=True)
                    # cursor.execute("""SELECT sub.Subtopics, s.read_status, s.watch_status FROM status AS s INNER JOIN subject AS sub ON s.text_id = sub.id WHERE s.student_name = %s """, (name,))
                    cursor = connection.cursor(dictionary=True)
                    cursor.execute("""
                        SELECT sub.Subtopics, MAX(s.read_status) AS read_status, MAX(s.read_timestamp) AS read_timestamp
                        FROM status AS s
                        INNER JOIN subject AS sub ON s.text_id = sub.id
                        WHERE s.student_name = %s
                        GROUP BY sub.Subtopics
                    """, (name,))
                    read_status_data = cursor.fetchall()
                    print("read_status_data",read_status_data)

                    cursor.execute("""
                        SELECT sub.Subtopics, MAX(s.watch_status) AS watch_status, MAX(s.watch_timestamp) AS watch_timestamp
                        FROM status AS s
                        INNER JOIN subject AS sub ON s.text_id = sub.id
                        WHERE s.student_name = %s
                        GROUP BY sub.Subtopics
                    """, (name,))
                    watch_status_data = cursor.fetchall()
                    print("watch_status_data",watch_status_data)

                    
                    cursor.close()

                    session['Subject'] = selected_subject
                    session['Chapter'] = selected_chapter
             
                    for read_status_row, watch_status_row in zip(read_status_data, watch_status_data):
                        subtopic_data = read_status_row['Subtopics']
                        read_status = bool(read_status_row['read_status'])
                        watch_status = bool(watch_status_row['watch_status'])
                        print("Subtopic:", subtopic_data)
                        
                        read_status_dt[read_status_row['Subtopics']] = read_status_row['read_status']
                        watch_status_dt[watch_status_row['Subtopics']] = watch_status_row['watch_status']
                        print("Subtopic:", subtopic_data)
                        print("Read Status:", "Yes" if read_status else "No")
                        print("Watch Status:", "Yes" if watch_status else "No")
                        print("Read Status Dt", read_status_dt)
                        print("Watch Status Dt", watch_status_dt)

                        subtopics_data.append(subtopic_data)
                        read_status_list.append("Yes" if read_status else "No")
                        watch_status_list.append("Yes" if watch_status else "No")

                        print("Read_Status", read_status)
                        print("Type of Read", type(read_status))
                    

                    connection.close()
                    return render_template('subtopics.html', user=get_user_info(), subtopics=subtopics, subject_level=subject_level, read_status=read_status, watch_status=watch_status, subtopics_data=subtopics_data, read_status_dt = read_status_dt, watch_status_dt = watch_status_dt)
                else:
                    return "Email or selected subject not found. Please check your session."
            except Exception as e:
                return "An error occurred: {}".format(str(e))
        else:
            return "Failed to establish MySQL connection. Please check your database settings."
    else:
        return render_template('subtopics.html', user=get_user_info(), subtopics=[], subject_level=None)
   
    
@app.route('/chapters', methods=['GET', 'POST'])
def chapters():
    selected_subject = None
    if request.method == 'POST':
        selected_subject = request.form['Chapter']
        session['selected_subject'] = selected_subject
        email = session.get('email')
        print(email)
        print(selected_subject)

    try:
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Query to retrieve chapters and descriptions for the selected subject
            cursor.execute("SELECT Chapter, ChapterDescription FROM subject WHERE Subject = %s", (selected_subject,))
            chapters = cursor.fetchall()
            
            # Fetching subject level            
            cursor.execute("SELECT DISTINCT SubjectLevel FROM score WHERE email = %s AND Subject = %s", (email, selected_subject))
            subject_level_result = cursor.fetchone()
            print(subject_level_result)
            subject_level_str = subject_level_result['SubjectLevel'] if subject_level_result and 'SubjectLevel' in subject_level_result else None
            subject_level = int(subject_level_str) if subject_level_str is not None else None
            print(subject_level)
            
            # Close cursor and connection
            cursor.close()
            connection.close()
            
            if chapters:
                # Pass the chapters data and subject level to the template
                return render_template('chapters.html',  user=get_user_info(), chapters=chapters, selected_subject=selected_subject, subject_level=subject_level)
            else:
                return "No chapters found for selected subject: {}".format(selected_subject)
    except Exception as e:
        return "An error occurred: {}".format(str(e))

    
@app.route('/textualcontent', methods=['GET', 'POST'])
def textualcontent():
    role = session.get('role')
    role = session.get('name')
    print("Role is:", role)

    if request.method == 'POST':
        subtopic = request.form['subject']
        print(request.form)

        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Construct and print the query for debugging
            query = "SELECT TextualContent, id FROM subject WHERE Subtopics = %s"
            
            # Execute the query with the subtopic value
            cursor.execute(query, (subtopic,))
            
            # Fetch the result
            textual_content = cursor.fetchone()

            # Fetch the text_id
            text_id = textual_content['id']

            session['text_id'] = text_id

            cursor.close()
            connection.close()

            # If textual content is found, render the template with it
            if textual_content:
                return render_template('textualcontent.html', textual_content=textual_content['TextualContent'], text_id=text_id, subtopic=subtopic, name = name,role=role, user = get_user_info)  # Pass 'subtopic' and 'text_id' to the template
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
    role = session.get('role')
    print("Role is:", role)
    
    if request.method == 'POST':
        subtopic = request.form['subject']
        
        # Connect to MySQL database
        connection = get_mysql_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            
            # Construct the query to fetch video content
            query = "SELECT Video, id FROM subject WHERE Subtopics = %s"
            
            # Execute the query with the subtopic value
            cursor.execute(query, (subtopic,))
            
            # Fetch the result
            video_content = cursor.fetchone()

            # Fetch the video_content_id
            video_content_id = video_content['id']
            print("This is the video content id:", video_content_id)

            session['video_content_id'] = video_content_id
            
            cursor.close()
            connection.close()

            # If video content is found, construct the iframe URL and render the template with it
            if video_content:
                # Extract the video ID from the URL
                video_id = extract_video_id(video_content['Video'])
                iframe_url = f"https://www.youtube.com/embed/{video_id}"
                
                # Get transcript for the video
                transcript = get_transcript(video_id)
                print(transcript)
                
                return render_template('videocontent.html', iframe_url=iframe_url, transcript=transcript, video_content_id=video_content_id, subtopic=subtopic, role=role)
            else:
                return "No video content found for this subtopic: " + subtopic  # Return the subtopic for debugging
        else:
            return "Failed to establish MySQL connection. Please check your database settings."
    else:
        return render_template('videocontent.html', role=role)  # Pass None if it's a GET request


@app.route('/progress_report', methods=['GET'])
def progress_report():
    email = session.get('email')
    name = session.get('name')
    role = session.get('role')
    print('Role:', role )
    students_list = {}
    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)
       
    # Query to retrieve subject names
    cursor.execute("SELECT DISTINCT Subject FROM subject")
    subjects_list= cursor.fetchall()

    cursor.execute("SELECT Subject, Subtopics FROM subject")
    topics_list= cursor.fetchall()

    # Query to retireve 
    query = "SELECT DISTINCT Subject, SubjectLevel FROM score WHERE email = %s"
    cursor.execute(query, (email,))
    user_subject_levels_list = cursor.fetchall()   

    query = "SELECT DISTINCT Subject, Topic, TopicScore, TopicLevel, tries FROM score WHERE email = %s AND Topic IS NOT NULL AND Topic != '-' ;"
    cursor.execute(query, (email,))
    user_topics_levels_list = cursor.fetchall()    
    
    return render_template('dump.html',name=name, email=email, role=role, subjects_list = subjects_list, user_subject_levels_list = user_subject_levels_list,
                          user_topics_levels_list = user_topics_levels_list, topics_list = topics_list, user=get_user_info())

@app.route('/student_report', methods=['GET'])
def progress_report_student():
    email = session.get('email')
    name = session.get('name')
    role = session.get('role')
    print('Role:', role )

    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)    
  
    # Query to retrieve subject names
    cursor.execute("SELECT DISTINCT Subject FROM subject")
    subjects_list= cursor.fetchall()

    cursor.execute("SELECT Subject, Subtopics FROM subject")
    topics_list= cursor.fetchall()

    # Query to retireve 
    query = "SELECT DISTINCT Subject, SubjectLevel, email FROM score"
    cursor.execute(query)
    user_subject_levels_list = cursor.fetchall()   

    query = "SELECT DISTINCT Subject, Topic, TopicScore, TopicLevel, tries, email FROM score WHERE Topic IS NOT NULL AND Topic != '-' ;"
    cursor.execute(query)
    user_topics_levels_list = cursor.fetchall()    

    query = "SELECT email, name FROM auth WHERE role ='Student';"
    cursor.execute(query)
    users_list = cursor.fetchall()
    
    return render_template('dump2.html',name=name, email=email, role=role, subjects_list = subjects_list, user_subject_levels_list = user_subject_levels_list,user_topics_levels_list = user_topics_levels_list, topics_list = topics_list, users_list = users_list, user=get_user_info())




@app.route('/topics_listing')
def topics_listing():
    return render_template('topics_listing.html')

@app.route('/topics-detail')
def topics_detail():
    return render_template('topics-detail.html')

@app.route('/contact')
def contact():
    return render_template('contact.html', user=get_user_info())

@app.route('/test')
def test():
    return render_template('test.html')

def get_subjects_and_topics_from_database():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="capstone"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT Subject, Subtopics FROM subject")
        subjects_and_topics = cursor.fetchall()
        cursor.close()
        connection.close()
        subjects = list(set(row[0] for row in subjects_and_topics))
        topics = list(set(row[1] for row in subjects_and_topics))
        return subjects, topics
    except mysql.connector.Error as err:
        print("Error retrieving subjects and topics from the database:", err)
        return [], []
    
subjects, topics = get_subjects_and_topics_from_database()
# -----------------------------------------------------
# ADAPTIVE LEARNING 
adaptive_model = AdaptiveLearningModel(subjects, topics)

@app.route('/mcq')
def mcq():
    global subjects
    connection = get_mysql_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        # Query to retrieve subject names
        cursor.execute("SELECT DISTINCT Subject FROM subject")
        subjects1 = cursor.fetchall()

        cursor.close()
        connection.close()

        # Inject user levels into template context
        user_levels = inject_user_level()['user_levels']
    
        progress = inject_user_topic_level()['progress']

        # Pass the subjects data and user levels to the template
        return render_template('mcq.html', subjects=subjects1, user_levels=user_levels, user=get_user_info(), progress= progress )

@app.context_processor
def inject_user_level():
    email = session.get('email')
    user_levels = {}

    if email:
        connection = get_mysql_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Query to retrieve user levels for each subject directly using email
                query = "SELECT Subject, SubjectLevel FROM score WHERE Email = %s"
                cursor.execute(query, (email,))
                user_levels_data = cursor.fetchall()

                for row in user_levels_data:
                    user_levels[row['Subject']] = row['SubjectLevel']

            except Error as e:
                print(f"Error executing MySQL query: {e}")

            finally:
                cursor.close()
                connection.close()

    return {'user_levels': user_levels}

# INJECTING LIST OF TOPIC USER HAS DONE 
@app.context_processor
def inject_user_topic_level():
    email = session.get('email')
    user_topic_done = {}
    total_topic ={}
    progress = {}


    if email:
        connection = get_mysql_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)

                # Query to retrieve user levels for each subject directly using email
                query = "SELECT Subject, Topic, COUNT(Topic) AS Total_Subtopics_Done FROM score WHERE email = %s AND Topic IS NOT NULL AND Tries = 1 GROUP BY Subject, Topic"
                cursor.execute(query, (email,))
                user_levels_data = cursor.fetchall()

                for row in user_levels_data:
                    user_topic_done[row['Subject']] = row['Total_Subtopics_Done']

                query = "SELECT Subject, COUNT(Subtopics) AS Total_Subtopics FROM subject GROUP BY Subject;"
                cursor.execute(query)
                total_subjects_topics = cursor.fetchall()

                for i in total_subjects_topics:
                    total_topic[i['Subject']] = i['Total_Subtopics']

                for subs in user_topic_done:
                    if subs in total_topic:
                        progress[subs] = user_topic_done[subs] / total_topic[subs]


            except Error as e:
                print(f"Error executing MySQL query: {e}")

            finally:
                cursor.close()
                connection.close()
    return {'progress' : progress}

# ------------------------------------------------
@app.route('/takemcq', methods=['POST'])
def subject_detail():
    # Get the subject name from the form submission
    subject_name = request.form['subject']
    session['subject_name'] = subject_name

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
        print(subtopic_list)
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
        return render_template('premcq.html', user=get_user_info(),api_response=api_response ,notify = False, subject_name = subject_name)

    else:
        return "Failed to establish MySQL connection. Please check your database settings."

@app.route('/checkAns', methods=['POST'])
def ans():
    subject_name = session.get('subject_name')
    answerSelected = []
    for i in questionList:
        answerSelected.append(request.form[i])

    global answerList
    # Count the number of matched items
    matched_items = len(set(answerSelected) & set(answerList))
    print(matched_items)

    # Update the score of the user for the selected topic
    cursor = connection.cursor(dictionary=True)
    level = '1'
    email = session['email']   
    subject = subject_name
    score = matched_items
    if score < 3:
        pass
    elif score >=4 and score <=8: 
        level = '2'
    elif score >=9:
        level = '3'

    cursor.execute('INSERT INTO score (email, Subject, SubjectScore, Topic, TopicScore, SubjectLevel,TopicLevel, tries) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (email, subject, score, '-', 0, level, '-', 0))

    connection.commit()

    score = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('premcq.html', notify = True, matched_items = matched_items, level = level, subject =subject, user=get_user_info())

# FOR TOPIC 
@app.route('/takemcq_subtopics', methods=['POST'])
def subtopics_detail():        
        subtopic_name = request.form['subject']
        session['subtopic_name'] = subtopic_name
        print(subtopic_name)
        
        api_response = generate_pre_mcq(subtopic_name)

        global answerList
        answerList.clear()
        # Saving the answers in the list
        for i in api_response['questions']:
            answerList.append(i['answer'])
        print('PRE ANSWERS:',answerList)
        global questionList
        questionList.clear()
        # Saving the questions in the list
        for i in api_response['questions']:
            print(i['question'])
            questionList.append(i['question'])
            
        return render_template('postmcq.html', api_response=api_response ,notify = False,user=get_user_info())


@app.route('/checkAns_postmcq', methods=['POST'])
def postmcq_ans():
    # Retrieve the subject name from the session
    # subject_name = session.get('subject_name')
    subject_name = session.get('selected_subject')

    answerSelected = []
    for i in questionList:
        answerSelected.append(request.form[i])

    global answerList
    # Count the number of matched items
    matched_items = len(set(answerSelected) & set(answerList))
    print(matched_items)
    print('Answer Selected:', answerSelected)
    print('Actual answers: ', answerList)
    # Update the score of the user for the selected topic
    connection = get_mysql_connection()
    cursor = connection.cursor(dictionary=True)
    email = session['email']
    print('Sub:', subject_name)
    score = matched_items      
    print('You have scored:',score)
        # subtopic_name = request.form['subject']
    print(request.form)
    subtopic_name = session.get('subtopic_name')
    print('TOP', subtopic_name)
        
    # Retrieve the subject level from the score table
    # Fetching subject level            
    cursor.execute("SELECT DISTINCT SubjectLevel, SubjectScore FROM score WHERE email = %s AND Subject = %s", (email, subject_name))
    subject_level_result = cursor.fetchone()
    print(subject_level_result)

    subject_score_str = subject_level_result['SubjectScore'] if subject_level_result and 'SubjectScore' in subject_level_result else None
    subject_score = int(subject_score_str) if subject_score_str is not None else None
    print(subject_score)
    subject_level_str = subject_level_result['SubjectLevel'] if subject_level_result and 'SubjectLevel' in subject_level_result else None
    subject_level = int(subject_level_str) if subject_level_str is not None else None
    print(subject_level)
        # Determine the topic level based on the score and subject level
    if score < 3:
        topic_level = '1'
    elif score >= 3 and score < 8:
            topic_level = '2'
    elif score >= 8:
            topic_level = '3'  
    print('Intial: ',topic_level)

    if topic_level <= str(subject_level):
        if str(subject_level) == '3':
                topic_level = '3'
        elif  str(subject_level) == '2':
                topic_level = '2'   
    
    if topic_level >= str(subject_level):            
            if str(subject_level) == '1':
                topic_level = '2'
            elif  str(subject_level) == '2':
                topic_level = '2'

    print('Final: ',topic_level)

    # Fetching the maximum tries value
    cursor.execute("""
        SELECT MAX(tries) AS max_tries 
        FROM score 
        WHERE email = %s AND Subject = %s AND Topic = %s
    """, (email, subject_name, subtopic_name))
    max_tries_result = cursor.fetchone()

    # Incrementing the tries value or initializing with 1 if no existing record found
    if max_tries_result is not None and max_tries_result['max_tries'] is not None:
        max_tries = max_tries_result['max_tries']
        new_tries = max_tries + 1
    else:
        new_tries = 1
            
    print('new try: ', new_tries)
    # if new_tries <=5:
            # Inserting the record with the new tries value
  
    cursor.execute("""
                    INSERT INTO score (email, Subject, SubjectScore, Topic, TopicScore, SubjectLevel, TopicLevel, tries) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (email, subject_name, subject_score, subtopic_name, score, subject_level, topic_level, new_tries))
    
 
    connection.commit()
    score = cursor.fetchall()
    cursor.close()

                # Close the database connection
    connection.close()

        # Redirect or render a response as needed
    return render_template('postmcq.html', notify = True, matched_items = matched_items, subject_level = subject_level, topic_level = topic_level, user=get_user_info()) 

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
            session['id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
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

    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")

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
            title_div = result.find('div', class_="_2dibcm7")
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

    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")

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
        img_containers = div.find_all('div', class_="perseus-widget-container widget-nohighlight widget-block")
        print("In perseus")
        for img_container in img_containers:
            # Find the parent figure element
            figure_tag = img_container.find('figure', class_="perseus-image-widget")
            print("In perseus image-widget")
            if figure_tag:
                # Find the div with class "fixed-to-responsive zoomable svg-image" within the figure element
                div_tag = figure_tag.find('div', class_="fixed-to-responsive zoomable svg-image")
                print("In fixed to")
                if div_tag:
                    img_tag = div_tag.find_next('img')
                    print("In image tag")
                    if img_tag:
                        # Extract the image URL
                        print("In final layer")
                        img_url = img_tag['src']
                        print("Extracted img", img_url)
                        article_content.append({'type': 'image', 'url': img_url})

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

@app.route('/addcontent', methods=['GET','POST'])
def addcontent():
    topic = request.args.get('topic')
    chapterdescription = request.args.get('chapterdescription')
    subject = session.get('Subject')
    subtopic = session['Subtopic'] = topic
    chaptd = session['ChapterDescription'] = chapterdescription
    print("Subject:", subject)
    if topic:
        # Scrape articles
        articles = scrape_khan_academy_articles(topic)
        
        return render_template('addcontent.html', results=articles, topic=topic, subject=subject, subtopic = subtopic)
    else:
        return render_template('addcontent.html',subject=subject)

@app.route('/insert-content', methods=['POST'])
def insert_content():
    # Extract content from request
    article_content = json.loads(request.form.get('article_content'))
    
    # Retrieve chapter and subtopic from session
    subject = session['Subject']
    chapter = session['Chapter']
    subtopic1 = session['Subtopic']
    chapd1 = session['ChapterDescription']
    print("Voila", subject)
    print("Voila2", chapter)
    

    serialized_content = json.dumps(article_content, ensure_ascii=False).encode('utf8')

    article_content = json.loads(serialized_content)

    # Extract text content from each item in the list
    normal_text = ""
    for _, item in article_content:  # Unpack each element to get the item
        if item['type'] == 'text':
            normal_text += item['content'] + '\n'  

    connection = get_mysql_connection()
    # Insert content into subject table 
    with connection.cursor() as cursor:
        sql = "INSERT INTO subject (Subject, Chapter,Subtopics ,TextualContent) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (subject, chapter, subtopic1 ,normal_text))
        connection.commit()

    return render_template("addcontent.html", inserted = True)
   

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
        connection = get_mysql_connection()
        cursor = connection.cursor()
        try:
            cursor.execute('INSERT INTO auth (name, email, password, role) VALUES (%s, %s, %s, %s)', (name, email, password, role))
            connection.commit()
            message = 'User registered successfully'
        except mysql.connector.Error as e:
            message = f'Error: {e}'
        finally:
            connection.close()

        session['role'] = role
        session['id'] = id
        # Redirect to the login page upon successful registration
        return redirect(url_for('login'))    

    return render_template('register.html', message=message)

@app.route('/submit_reading_status', methods=['POST'])
def submit_reading_status():
    if request.method == 'POST':
        # Get student_id from session or wherever it's stored after authentication
        id = session.get('id')
        name = session.get('name')
        text_id = request.form.get('text_id')
        video_id = request.form.get('video_id')
        print("Text ID", text_id) 
        print("Video ID", video_id) 
        print("Name", name)
        
        # Check if student_id exists
        if not id:
            return 'Student ID not found. Please log in.'
        
        # Check if at least one of text_id or video_id exists
        if not text_id and not video_id:
            return 'No content ID provided.'

        # Update student_reading_status table
        # with connection.cursor() as cursor:
        #     if text_id:
        #         # Update read_status and read_timestamp for textual content
        #         cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        #         cursor.execute("INSERT INTO status (student_id, student_name, text_id, read_status, read_timestamp) VALUES (%s, %s, %s, TRUE, %s) ON DUPLICATE KEY UPDATE read_status = TRUE, read_timestamp = %s", (id, name, text_id, datetime.datetime.now(), datetime.datetime.now()))
        #     if video_id:
        #         # Update watch_status and watch_timestamp for video content
        #         cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
        #         cursor.execute("INSERT INTO status (student_id, student_name, video_id, watch_status, watch_timestamp) VALUES (%s, %s, %s, TRUE, %s) ON DUPLICATE KEY UPDATE watch_status = TRUE, watch_timestamp = %s", (id, name, video_id, datetime.datetime.now(), datetime.datetime.now()))
        # connection.commit()
        # return 'Reading status submitted successfully'
        # Update student_reading_status table
        with connection.cursor() as cursor:
            if text_id:
                # Check if a row exists for the given student and text_id
                cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
                cursor.execute("SELECT COUNT(*) FROM status WHERE student_id = %s AND text_id = %s", (id, text_id))
                row_count = cursor.fetchone()[0]
                if row_count > 0:
                    # Update read_status and read_timestamp for textual content
                    cursor.execute("""
                        UPDATE status 
                        SET read_status = TRUE, read_timestamp = %s
                        WHERE student_id = %s AND text_id = %s
                    """, (datetime.datetime.now(), id, text_id))
                else:
                    # Insert a new row for textual content
                    cursor.execute("""
                        INSERT INTO status (student_id, student_name, text_id, read_status, read_timestamp) 
                        VALUES (%s, %s, %s, TRUE, %s)
                    """, (id, name, text_id, datetime.datetime.now()))
            if video_id:
                # Check if a row exists for the given student and video_id
                cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
                cursor.execute("SELECT COUNT(*) FROM status WHERE student_id = %s AND video_id = %s", (id, video_id))
                row_count = cursor.fetchone()[0]
                if row_count > 0:
                    # Update watch_status and watch_timestamp for video content
                    cursor.execute("""
                        UPDATE status 
                        SET watch_status = TRUE, watch_timestamp = %s
                        WHERE student_id = %s AND video_id = %s
                    """, (datetime.datetime.now(), id, video_id))
                else:
                    # Insert a new row for video content
                    cursor.execute("""
                        INSERT INTO status (student_id, student_name, video_id, watch_status, watch_timestamp) 
                        VALUES (%s, %s, %s, TRUE, %s)
                    """, (id, name, video_id, datetime.datetime.now()))

        connection.commit()
        return 'Reading status submitted successfully'


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
        
def get_data_from_mysql(role):
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='capstone',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            data1 = data2 = data3 = data4 = None  # Initialize variables
            if role == 'Student':
                cursor.execute("SELECT Subject, SubjectScore FROM score")
                data1 = cursor.fetchall()
                cursor.execute("SELECT student_id, read_status, watch_status FROM status")
                data2 = cursor.fetchall()
            elif role == 'Teacher':
                cursor.execute("SELECT student_id, read_status, watch_status FROM status")
                data3 = cursor.fetchall()
                cursor.execute("SELECT Subject, SubjectScore FROM score")
                data4 = cursor.fetchall()
    finally:
        connection.close()
    return data1, data2, data3, data4

def generate_with_cohere(keyword):
    for event in co.chat(f"Explain {keyword} in 1000 words to me and give output in HTML format", stream=True):
        if event.event_type == cohere.responses.chat.StreamEvent.TEXT_GENERATION:
            generated_text = f"{event.text}"  # Wrap each line in a <p> tag for better formatting
            yield generated_text

        elif event.event_type == cohere.responses.chat.StreamEvent.STREAM_END:
            yield f""


# PROGRESS
@app.route('/subject_scores')
def subject_scores():
    # Connect to MySQL database
    conn = get_mysql_connection()
    cursor = conn.cursor()

    # Fetch data from the score table
    cursor.execute("SELECT Subject, AVG(SubjectScore) FROM score GROUP BY Subject")
    data = cursor.fetchall()

    # Close the connection
    cursor.close()
    conn.close()

    # Prepare data for Chart.js
    labels = [row[0] for row in data]
    scores = [float(row[1]) for row in data]

    return jsonify(labels=labels, scores=scores)





if __name__ == '__main__':
    connection = get_mysql_connection()
    if connection:
        app.secret_key = 'your_secret_key'
        # If connection is successful, run the Flask application
        app.run(debug=True)
    else:
        # If connection fails, print an error message
        print("Failed to establish MySQL connection. Exiting.")
