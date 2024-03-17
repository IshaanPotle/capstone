from flask import Flask, render_template, request, Response
import time
import cohere

app = Flask(__name__, static_url_path='/static')
co = cohere.Client('WrwwKEMSMjFySzaPxE9NmECZ6gjs4cINUtioGtNF')

@app.route('/')
def index():
    return render_template('index.php')

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

@app.route('/login')
def login():
    return render_template('login.php')

@app.route('/register')
def register():
    return render_template('register.php')

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
    app.run(debug=True)
