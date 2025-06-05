import os

from dotenv import load_dotenv

def return_env():
    load_dotenv()
    env = os.environ.copy()
    return env