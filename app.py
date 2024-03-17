from flask import Flask, render_template, request, Response
import time
import cohere

app = Flask(__name__, static_url_path='/static')
co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

@app.route('/')
def index():
    return render_template('index.html')

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
def test_html():
    return render_template('test.html')

@app.route('/generate', methods=['POST'])
def test_results_html():
    keyword = request.form['keyword']
    return Response(generate_with_cohere(keyword), content_type='text/event-stream')

def generate_with_cohere(keyword):
    for event in co.chat(f"Generate only 10 MCQ questions based on the given passage and Mark Answers and convert to a JSON format {{'Question': '{{Actual Question}}', 'Answer' : '{{Actual Answer}}', 'Distractor': [\'Option1\', \'Option2\',\'Option3\', \'Option4\']}} :{keyword} ", stream=True):
        if event.event_type == cohere.responses.chat.StreamEvent.TEXT_GENERATION:
            generated_text = f"{event.text}"  # Wrap each line in a <p> tag for better formatting
            yield f"<pre>{generated_text}</pre>"
    
        elif event.event_type == cohere.responses.chat.StreamEvent.STREAM_END:
            yield f""

def generate_html(json_text):
    # Parse the JSON text
    data = json.loads(json_text)
    
    # Initialize an empty HTML string
    html = ""
    
    # Loop through each item in the JSON data
    for item in data:
        # Add the question with appropriate styling
        html += f"<span class='question'>{item['Question']}</span><br>"
        
        # Add the answer with appropriate styling
        html += f"<span class='answer'>{item['Answer']}</span><br>"
        
        # Add the distractors with appropriate styling
        html += "<span class='distractor'>Distractors:</span><br>"
        for distractor in item['Distractor']:
            html += f"<span class='distractor'>{distractor}</span><br>"
        
        # Add a separator between items
        html += "<hr>"
    
    return html



if __name__ == '__main__':
    app.run(debug=True)
