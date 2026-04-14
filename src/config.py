import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.environ["DATABASE_URL"]
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]
APIFY_API_TOKEN: str = os.environ["APIFY_API_TOKEN"]
