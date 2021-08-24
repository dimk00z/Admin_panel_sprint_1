from pathlib import Path
from os import getenv
from dotenv import load_dotenv


def load_params(required_params):
    load_dotenv()
    return {param.lower(): getenv(param)
            for param in required_params}
