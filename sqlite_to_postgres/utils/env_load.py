from pathlib import Path
from os import getenv
from dotenv import load_dotenv


def load_params(required_params):
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    return {param.lower(): getenv(param)
            for param in required_params}
