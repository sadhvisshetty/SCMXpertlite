import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .auth import get_current_user_from_cookie
from .routers import router
from .config import templates
import uvicorn

app = FastAPI()


# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Templates directory
templates_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "templates"))
templates = Jinja2Templates(directory=templates_dir)

# Static files directory
static_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "static"))
if not os.path.isdir(static_dir):
    raise RuntimeError(f"Static directory does not exist: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Image files directory
image_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "images"))
if not os.path.isdir(image_dir):
    raise RuntimeError(f"Image directory does not exist: {image_dir}")

app.mount("/images", StaticFiles(directory=image_dir), name="images")

# Include routers
app.include_router(router)


# Routes
@app.get("/forgot", response_class=HTMLResponse)
async def get_forgot_password(request: Request):
    return templates.TemplateResponse("forgotPassword.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("Home.html", {"request": request})


@app.get("/Login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("Login.html", {"request": request})


@app.get("/signUp", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, user=Depends(get_current_user_from_cookie)):
    response = templates.TemplateResponse("dashboard.html", {"request": request, "user": user})
    # Disable caching for this route
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/myShipment", response_class=HTMLResponse)
async def get_my_shipment(request: Request, user=Depends(get_current_user_from_cookie)):
    
    headings = ["Shipment ID", "Status", "Date", "Destination"]
    data = [
        ["001", "In Transit", "2025-07-28", "New York"],
        ["002", "Delivered", "2025-07-26", "Los Angeles"],
    ]
    header = "My"
    Shipments = "Your shipment data will be displayed here." # NOSONAR
    return templates.TemplateResponse(
        "myShipment.html",
        {
            "request": request,
            "user": user,
            "headings": headings,
            "data": data,
            "header": header,
            "Shipments": Shipments
        }
    )



@app.get("/shipment", response_class=HTMLResponse)
async def get_shipment(request: Request, user=Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("shipment.html", {"request": request, "user": user})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/Login")
    # Delete the cookie on logout
    response.delete_cookie(key="access_token")  
    return response

if __name__ == "__main__":
    
    uvicorn.run("app.backend.main:app", host="0.0.0.0", port=8000, reload=True)



