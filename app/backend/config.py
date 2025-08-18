import os
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
# Go up one level (to app), then into frontend/templates
templates_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "templates"))

templates = Jinja2Templates(directory=templates_dir)
