
from flask import Flask, render_template, request, send_file
from datetime import datetime
import openai
import pdfkit
import os

app = Flask(__name__)

openai.api_key = "YOUR_OPENAI_API_KEY"

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/generate', methods=['POST'])
def generate():
    crop = request.form['crop']
    area = request.form['area']
    location = request.form['location']
    purpose = request.form['purpose']
    client = request.form['client']

    prompt = f"""
    다음 조건에 맞는 스마트팜 제안서를 작성해줘:
    - 작물: {crop}
    - 면적: {area} 제곱미터
    - 지역: {location}
    - 목적: {purpose}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message['content']
    except Exception as e:
        result = f"AI 응답 오류: {e}"

    html = render_template("template.html",
        crop=crop, area=area, location=location, purpose=purpose,
        content=result, client=client
    )

    filename = f"proposal_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"

    options = {
        'encoding': "UTF-8",
        'enable-local-file-access': ''
    }

    pdfkit.from_string(html, filename, options=options)

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
