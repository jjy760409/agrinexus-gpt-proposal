from flask import Flask, render_template, request, send_file
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
import pdfkit
import os

app = Flask(__name__)

# OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Email config (example using Gmail SMTP)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("MAIL_USER"),
    MAIL_PASSWORD=os.getenv("MAIL_PASS")
)
mail = Mail(app)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client = db.Column(db.String(100))
    crop = db.Column(db.String(100))
    area = db.Column(db.String(100))
    location = db.Column(db.String(100))
    purpose = db.Column(db.String(200))
    email = db.Column(db.String(100))
    language = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
    email = request.form['email']
    language = request.form['language']

    db.session.add(Submission(
        client=client, crop=crop, area=area, location=location,
        purpose=purpose, email=email, language=language
    ))
    db.session.commit()

    base_prompt = f"""
    Create a smart farm proposal for:
    - Crop: {crop}
    - Area: {area} m²
    - Location: {location}
    - Purpose: {purpose}
    Respond in {language} language.
    Provide full proposal and a 3-line executive summary.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": base_prompt}]
        )
        result = response.choices[0].message['content']
        if "Summary:" in result:
            parts = result.split("Summary:")
            summary = parts[1].strip().split("\n")[0]
            content = parts[0].strip()
        else:
            summary = "요약 정보가 제공되지 않았습니다."
            content = result
    except Exception as e:
        summary = "GPT 오류 발생"
        content = str(e)

    html = render_template("template.html",
        crop=crop, area=area, location=location, purpose=purpose,
        content=content, client=client, summary=summary
    )

    filename = f"proposal_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdfkit.from_string(html, filename, options={'encoding': "UTF-8", 'enable-local-file-access': ''})

    try:
        msg = Message("AgriNexus GPT 제안서", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = "첨부된 PDF 제안서를 확인해 주세요."
        with app.open_resource(filename) as fp:
            msg.attach(filename, "application/pdf", fp.read())
        mail.send(msg)
    except Exception as e:
        print("메일 전송 실패:", e)

    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=10000)