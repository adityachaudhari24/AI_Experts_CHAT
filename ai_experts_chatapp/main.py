from .server import app
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
      uvicorn.run(app, port=8000, host="0.0.0.0")