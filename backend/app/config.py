import os
from dotenv import load_dotenv

load_dotenv()

COC_API_TOKEN = os.getenv("COC_API_TOKEN")
BASE_URL = "https://api.clashofclans.com/v1"

if not COC_API_TOKEN:
    raise RuntimeError("COC_API_TOKEN no está definido")
