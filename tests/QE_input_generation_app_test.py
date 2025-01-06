import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/qe_input')))

from streamlit.testing.v1 import AppTest
from dotenv import load_dotenv
import os

# load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")


def test_app():
    at = AppTest(script_path="src/qe_input/QE_input_generation_app.py", default_timeout=10)
    at.run()
    assert not at.exception

