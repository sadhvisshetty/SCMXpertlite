from fastapi import APIRouter, Depends, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import EmailStr
from datetime import timedelta
from bson import ObjectId
from .models import User, Shipment, DeviceData
from .db import user_collection, shipment_collection, device_collection
from .auth import get_current_user_from_cookie, RoleChecker
from .utils import hash_password, verify_password, create_access_token, generate_otp, MessageSchema
from .forgot import router as forgot_router
from .forgot import router as forgot_router, send_otp_email,send_account_deleted_email, EMAIL_ADDRESS, EMAIL_PASSWORD
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.responses import HTMLResponse
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime, timezone
from .models import Shipment






router = APIRouter()
router.include_router(forgot_router)

# OTP in-memory store: {email: otp}
otp_store = {}



# Signup route
@router.post("/signUp", status_code=201)
async def signup(user: User):
    existing = await user_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_data = user.model_dump()
    user_data["role"] = "User"  
    user_data["permissions"] = ["User"]
    user_data["password"] = hash_password(user.password)

    await user_collection.insert_one(user_data)
    return {"message": "Signup successful"}

# Login route
@router.post("/Login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await user_collection.find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": user["email"], "role": user.get("role", "User")},
        expires_delta=timedelta(hours=1)
    )

    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False  
    )
    return response


@router.get("/myShipment", response_class=HTMLResponse)
async def get_my_shipment(request: Request, user=Depends(get_current_user_from_cookie)):
    from .main import templates 
    user_email = user.get("email")

    cursor = shipment_collection.find({"uemail": user_email})
    shipments = []
    async for shipment in cursor:
        shipment["_id"] = str(shipment["_id"])  # Convert ObjectId to str for template
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
            "headers": headers
        }
    )

# Shipment route (Admin/User role)

@router.post("/shipment")
async def create_shipment(shipment: Shipment, user=Depends(RoleChecker(["Admin", "User"]))):
    
    shipment_data = shipment.model_dump()  # Convert Pydantic model to dict
    
    # Inject logged-in user's info BEFORE inserting
    shipment_data["uname"] = user.get("username")  
    shipment_data["uemail"] = user.get("email")    

    if len(str(shipment_data["ShipNum"])) > 7:
        raise HTTPException(status_code=400, detail="Shipment number length cannot exceed 7 digits.")

    existing_shipment = await shipment_collection.find_one({"ShipNum": shipment_data["ShipNum"]})
    if existing_shipment:
        raise HTTPException(status_code=400, detail="Shipment number already exists.")

    try:
        exp_date = datetime.strptime(shipment_data["ExpDelDate"], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Expected delivery date format must be YYYY-MM-DD.")

    today = datetime.now(timezone.utc).date()
    if exp_date < today:
        raise HTTPException(status_code=400, detail="Expected delivery date cannot be in the past.")

    await shipment_collection.insert_one(shipment_data)

    return {"message": "Shipment data saved"}
# Device data route (Admin role only)
@router.post("/deviceData")
async def device_data(data: DeviceData, user=Depends(RoleChecker(["Admin"]))):
    await device_collection.insert_one(data.model_dump())
    return {"message": "Device data submitted"}



# Login OTP request (send OTP email)
@router.post("/login/request-otp")
async def request_login_otp(email: EmailStr):
    otp = generate_otp()
    otp_store[email] = otp
    send_otp_email(email, otp)
    return {"message": "OTP sent"}



# Login OTP verification
@router.post("/login/verify-otp")
async def verify_login_otp(email: EmailStr, otp: str):
    if otp_store.get(email) == otp:
        otp_store.pop(email, None)
        return {"message": "OTP verified - login success"}
    raise HTTPException(status_code=401, detail="Invalid OTP")



# Get current logged-in user info (HTML response)
@router.get("/MyAccount", response_class=HTMLResponse)
async def get_my_account_page(request: Request, user=Depends(get_current_user_from_cookie)):
    from .main import templates
    from .db import shipment_collection

    if "_id" in user:
        user["_id"] = str(user["_id"])

    # 🔍 DEBUG: Print all shipments in DB
    print("=== ALL SHIPMENTS ===")
    cursor = shipment_collection.find({})
    async for doc in cursor:
        print(doc)

    # 🧮 Count how many shipments belong to this user
    user_email = user.get("email")
    shipment_count = await shipment_collection.count_documents({"uemail": user_email})
    print(f"Shipment count for {user_email}:", shipment_count)

    return templates.TemplateResponse("myAccount.html", {
        "request": request,
        "user": user,
        "shipmentCount": shipment_count
    })




# Get current logged-in user info (JSON response)
@router.get("/myAccount", response_class=JSONResponse)
async def get_my_account_data(user=Depends(get_current_user_from_cookie)):
    user_email = user.get("email")
    shipment_count = await shipment_collection.count_documents({"uemail": user_email})

    return {
        "username": user.get("username", "No name"),
        "email": user_email or "No email",
        "shipmentCount": shipment_count
    }


# Delete user (Admin only)
@router.delete("/user/{user_id}", dependencies=[Depends(RoleChecker(["Admin"]))])
async def delete_user(user_id: str):
    user = await user_collection.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await user_collection.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 1:
        # Send notification email
        send_account_deleted_email(user["email"])
        return {"message": "User deleted and notified."}

    raise HTTPException(status_code=500, detail="User could not be deleted.")


#to check all the users by admin
@router.get("/users", dependencies=[Depends(RoleChecker(["Admin"]))])
async def get_all_users():
    users_cursor = user_collection.find({})
    users = []
    async for user in users_cursor:
        users.append({
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role", "User")
        })
    return users




# Signup OTP request (send OTP email)
@router.post("/signup/request-otp")
async def signup_request_otp(request: Request, email: str = Form(...)):
    from .main import templates  
    otp = generate_otp()
    otp_store[email] = otp
    send_otp_email(email, otp)

    return templates.TemplateResponse("signUp.html", {
        "request": request,
        "message": "OTP sent to your email.",
        "email": email
    })
