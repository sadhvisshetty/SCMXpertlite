import os
from fastapi.staticfiles import StaticFiles
import uvicorn

from .main import app as main_app  

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.abspath(os.path.join(current_dir, "templates"))
static_dir = os.path.abspath(os.path.join(current_dir, "static"))

# Mount static files at /static
main_app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount templates folder to serve HTML files at root
main_app.mount("/", StaticFiles(directory=templates_dir, html=True), name="templates")

if __name__ == "__main__":
    uvicorn.run(main_app, host="127.0.0.1", port=8000)
