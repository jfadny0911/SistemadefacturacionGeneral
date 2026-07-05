import os
from dotenv import load_dotenv

load_dotenv()

print("HOST:", os.getenv("DB_HOST"))
print("USER:", os.getenv("DB_USER"))
print("PASSWORD:", os.getenv("DB_PASSWORD"))
