import PyPDF2
import speech_recognition as sr
import pyttsx3
import requests
import re
import time

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text)

def extract_text_from_pdf(pdf_path, num_pages=None):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for i, page in enumerate(reader.pages):
            if num_pages and i >= num_pages:
                break
            text += page.extract_text()
    return text

def get_gemini_response(query, context, retries=3, delay=5):
    api_key = 'AIzaSyAjjoix-hOJCKnMD8hofwVgS4QBCt6HzPU'
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'contents': [{
            'parts': [{
                'text': f"Context: {context}\nQuestion: {query}"
            }]
        }]
    }
    for attempt in range(retries):
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            print('Full API Response:', response_json)
            
            if 'candidates' in response_json and len(response_json['candidates']) > 0:
                content = response_json['candidates'][0].get('content', {})
                parts = content.get('parts', [])
                if len(parts) > 0:
                    raw_text = parts[0].get('text', 'No text found in response')
                    cleaned_text = clean_text(raw_text)
                    return cleaned_text
            return 'No response from Gemini API'
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                print(f'Request Error: {e}. Retrying in {delay} seconds...')
                time.sleep(delay)
                delay *= 2  
            else:
                return f'Request Error: {e}'

def test_text_to_speech(text):
    engine.say(text)
    engine.runAndWait()


pdf_path = 'E:\MyProjects\Voiceassistant\portion.pdf'
pdf_text = extract_text_from_pdf(pdf_path, num_pages=10)

while True:
    with sr.Microphone() as source:
        print('Clearing background noise...Please wait')
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Waiting for your message...")
        recorded_audio = recognizer.listen(source)
        print('Done recording')

    try:
        print('Printing your message...Please wait')
        text = recognizer.recognize_google(recorded_audio, language='en-US')
        print(f'Your Message: {text}')
        
        if text.lower() == 'terminate':
            print('Goodbye!')
            break
        
        gemini_response = get_gemini_response(text, pdf_text)
        print(f'Gemini Response: {gemini_response}')
        
        test_text_to_speech(gemini_response)

    except Exception as ex:
        print(f'Error: {ex}')
