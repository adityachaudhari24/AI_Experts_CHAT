# AI_Experts_CHAT
AI_Experts_CHAT



Steps to setup 

1. Install python on your system if not installed.
2. create the venv and activate
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```
3. 3. Install the required dependencies:
```bash
pip install -r requirements.txt
```
freez your requirments if required `pip freeze > requirements.txt`


4. Create a `.env` file in the project directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

The application consists of two components: the FastAPI backend and the Streamlit frontend. You'll need to run both components.

1. Start the FastAPI backend server: 
Do execute `fastapi dev server.py` if you see error try installing it with `pip install "fastapi[standard]" `
```bash
python main.py
```

There is one more way as we have istalled the uvicorn and we have main function you can go to root folder and execute this command to start the backend server . `python -m ai_experts_chatapp.main`

The backend server will start on http://localhost:8000

