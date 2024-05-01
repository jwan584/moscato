from flask import Flask, request, render_template
from markupsafe import Markup
import requests
from newspaper import Article
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()

# Access the API keys using os.environ.get()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

def fetch_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        return response
    except requests.exceptions.RequestException as e:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if request.form.get('summarize'):
            raw_content = get_url_content(url)
            summary = generate_summary_llm(raw_content)
            return render_template('index.html', summary=summary)
        elif request.form.get('show_input'):
            raw_content = get_url_content(url)
            return render_template('index.html', raw_input=raw_content)
        elif request.form.get('show_raw'):
            raw_url_content = get_raw_url_content(url)
            return render_template('index.html', raw_url=raw_url_content)
        else:
            return render_template('index.html', summary='', raw_input='')
    return render_template('index.html')

def get_url_content(url):
    response = fetch_url(url)
    if response is not None:
        try:
            article = Article(url)
            article.download(input_html=response.text)
            article.parse()
            title = article.title
            content = f"Title: {title}\n\n{article.text}"
            return content
        except Exception as e:
            return f"Error: {e}"
    else:
        return "Failed to fetch the URL content."

def generate_summary_llm(content):
    try:
        anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"""\n\nHuman: You are a savvy writer known for giving engaging and illuminating
                explainations. Give a user friendly summary this article explaining the key points
                in bullets. The first bullet is a high level summary of article with context. Eg.
                "This is a news report about the war in ukraine" or "This is a launch blog for a new
                shampoo." or "This blog makes the case for the benefits of carbon credits."
                Format your response in HTML \n\n{content}\n\nAssistant:"""
        response = anthropic.completions.create(
            prompt=prompt,
            max_tokens_to_sample=600,
            model="claude-v1",
            temperature=0.5,
            top_p=0.9,
            stop_sequences=["\n\nHuman:"]
        )
        summary = response.completion.strip()
        return Markup(summary)
    except (requests.exceptions.RequestException, Exception) as e:
        return f"Error: {e}"

def get_raw_url_content(url):
    response = fetch_url(url)
    if response is not None:
        return response.text
    else:
        return "Failed to fetch the raw URL content."

if __name__ == '__main__':
    app.run(debug=True, port=8132)