python3 -m venv venv
source venv/bin/activate
pip install python-dotenv
pip freeze > requirements.txt
pip install openai
pip install -r requirements.txt