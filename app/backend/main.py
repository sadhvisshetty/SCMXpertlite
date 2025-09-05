import os
from fastapi import FastAPI, Request, Depends,HTTPException
from fastapi.responses import HTMLResponse,RedirectResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from .auth import get_current_user_from_cookie
from .db import shipment_collection
from .routers import router
from .config import templates
import uvicorn

app = FastAPI()

frontend_url = os.getenv("URL")
print('hello')
print(frontend_url)
#CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],  
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

@app.exception_handler(HTTPException)
async def custom_unauthenticated_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        html_content = """
        <html>
            <body>
                <h2>Please login to access the pages</h2>
                <a href="/Login">Go to Login</a>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content, status_code=401)
    else:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# Routes
@app.get("/forgot", response_class=HTMLResponse)
async def get_forgot_password(request: Request):
    return templates.TemplateResponse("forgotPassword.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/Login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("Login.html", {"request": request})


@app.get("/signUp", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signUp.html", {"request": request})


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
    if user.get("role") == "Admin":
        # Admin: fetch all shipments
        cursor = shipment_collection.find()
    else:
        # Normal user: fetch only their shipments by email
        cursor = shipment_collection.find({"uemail": user.get("email")})

    shipments = []
    async for shipment in cursor:
        shipment["_id"] = str(shipment["_id"])  
        shipments.append(shipment)

    headers = [
        "Shipment Number", "Username", "Email", "Route Details", "Device",
        "PO Number", "NDC Number", "Serial Number", "Container Number",
        "Goods Type", "Expected Delivery Date", "Delivery Number", "Batch ID", "Shipment Description"
    ]

    return templates.TemplateResponse(
        "myShipment.html",
        {
            "request": request,
            "user": user,
            "shipments": shipments,
            "headers": headers,
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



