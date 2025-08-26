from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import JSONResponse,HTMLResponse
from pydantic import EmailStr
from datetime import timedelta,datetime,timezone
from bson import ObjectId
from .models import User, Shipment, DeviceData
from .db import user_collection, shipment_collection, device_collection
from .auth import get_current_user_from_cookie, RoleChecker
from .utils import hash_password, verify_password, create_access_token, generate_otp
from .forgot import router as forgot_router, send_otp_email,send_account_deleted_email, send_role_change_email,EMAIL_ADDRESS, EMAIL_PASSWORD
from bson.errors import InvalidId
from .config import templates
from fastapi import Body


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

#Login route with RBAC
@router.post("/Login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # If user is admin
    if user.get("role") != "Admin":
        if not verify_password(password, user["password"]):
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

    if user.get("role") == "Admin":
        cursor = shipment_collection.find({})
    else:
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
            "headers": headers
        }
    )


# Shipment route (Admin/User role)

@router.post("/shipment")
async def create_shipment(shipment: Shipment, user=Depends(RoleChecker(["Admin", "User"]))):
    
    shipment_data = shipment.model_dump()  
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



# Get current logged-in user info 
@router.get("/MyAccount", response_class=HTMLResponse)
async def get_my_account_page(request: Request, user=Depends(get_current_user_from_cookie)):
    from .main import templates
    from .db import shipment_collection

    if "_id" in user:
        user["_id"] = str(user["_id"])
    print("=== ALL SHIPMENTS ===")
    cursor = shipment_collection.find({})
    async for doc in cursor:
        print(doc)
    user_email = user.get("email")
    shipment_count = await shipment_collection.count_documents({"uemail": user_email})
    print(f"Shipment count for {user_email}:", shipment_count)

    return templates.TemplateResponse("myAccount.html", {
        "request": request,
        "user": user,
        "shipmentCount": shipment_count
    })




# Gets current logged-in user info
@router.get("/myAccount", response_class=JSONResponse)
async def get_my_account_data(user=Depends(get_current_user_from_cookie)):
    user_email = user.get("email")
    shipment_count = await shipment_collection.count_documents({"uemail": user_email})

    return {
        "username": user.get("username", "No name"),
        "email": user_email or "No email",
        "shipmentCount": shipment_count
    }

#For RBAC control by Admin
@router.put("/user/{user_id}/role", dependencies=[Depends(RoleChecker(["Admin"]))])
async def update_user_role(user_id: str, new_role: str = Body(..., embed=True)):
    from bson import ObjectId
    from bson.errors import InvalidId

    if new_role not in ["User", "Admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await user_collection.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update role and permissions
    update_result = await user_collection.update_one(
        {"_id": user_obj_id},
        {"$set": {"role": new_role, "permissions": [new_role]}}
    )
    if update_result.modified_count != 1:
        raise HTTPException(status_code=500, detail="Failed to update role")

    # Send notification email
    try:
        send_role_change_email(user["email"], new_role)
    except Exception as e:
        print(f"Failed to send role change email: {e}")

    return {"message": f"User role updated to {new_role}"}


# Delete user (Admin only)
@router.delete("/user/{user_id}", dependencies=[Depends(RoleChecker(["Admin"]))])
async def delete_user(user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user = await user_collection.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await user_collection.delete_one({"_id": user_obj_id})
    if result.deleted_count != 1:
        raise HTTPException(status_code=500, detail="User could not be deleted")

    try:
        send_account_deleted_email(user["email"])
    except Exception:
        pass 

    return {"message": "User deleted and notified."}


#to check all the users by admin
@router.get("/users", dependencies=[Depends(RoleChecker(["Admin"]))])
async def get_all_users():
    users_cursor = user_collection.find({})
    users = []
    async for user in users_cursor:
        shipment_count = await shipment_collection.count_documents({"uemail": user.get("email")})
        users.append({
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role", "User"),
            "shipment_count": shipment_count
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
@router.get("/deviceData", response_class=HTMLResponse)
async def show_device_data(request: Request, user=Depends(get_current_user_from_cookie)):
    try:
        if not user or user.get("role") != "Admin":
            return templates.TemplateResponse("page_not_found.html", {
                "request": request,
                "message": "Access Denied"
            })

        cursor = device_collection.find().sort("_id", -1).limit(50)
        devices_raw = []
        async for doc in cursor:
            devices_raw.append(doc)

        devices = []
        device_ids_set = set()

        for d in devices_raw:
            device = {
                "deviceId": d.get("Device_Id", ""),  
                "batteryLevel": d.get("Battery_Level", ""),
                "temperature": d.get("First_Sensor_temperature", ""),
                "routeFrom": d.get("Route_From", ""),
                "routeTo": d.get("Route_To", "")
            }
            devices.append(device)
            if device["deviceId"]:
                device_ids_set.add(device["deviceId"])

        device_ids = sorted(device_ids_set)

        return templates.TemplateResponse("deviceData.html", {
            "request": request,
            "user": user,
            "devices": devices,
            "device_ids": device_ids
        })

    except Exception as e:
        print(f"Error in show_device_data: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "Something went wrong while loading device data."
        })

