from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from .db import user_collection
from .utils import hash_password
import random
import string
import smtplib
import traceback
import os
from dotenv import load_dotenv
from email.message import EmailMessage

templates = Jinja2Templates(directory="../frontend/templates")
from fastapi.responses import JSONResponse

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

FORGOT_PASSWORD_TEMPLATE = "forgotPassword.html"
LOGIN_TEMPLATE = "Login.html"

router = APIRouter()

# In-memory store for OTPs
otp_store = {}

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(recipient_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg["Subject"] = "Your SCMXpert OTP Code for changing the Password"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"OTP sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
        traceback.print_exc()

def send_account_deleted_email(recipient_email: str):
    subject = "Account Deleted Notification"
    body = f"""
    Dear User,

    This is to inform you that your account associated with this email ({recipient_email}) has been deleted by the administrator.

    If you believe this was done in error, please contact support immediately.

    Regards,  
    SCMXpert Team
    Support - sadhvisshetty03@gmail.com
    """

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"Account deletion email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending deletion email: {e}")
        traceback.print_exc()



@router.post("/forgotpass/request", response_class=HTMLResponse)
async def forgot_password_request(request: Request, email: str = Form(...)):
    try:
        user = await user_collection.find_one({"email": email})

        if not user:
            # Detect AJAX request
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JSONResponse(status_code=400, content={"error": "Email not registered."})

            return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
                "request": request,
                "detail": "Email not registered.",
                "email": email
            })

        otp = generate_otp()
        otp_store[email] = otp
        send_otp_email(email, otp)

        # Return JSON if called from JS
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(content={"message": f"OTP sent to {email} successfully."})

        # Else fallback to HTML page
        return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
            "request": request,
            "message": f"OTP sent to {email} successfully.",
            "email": email
        })

    except Exception as e:
        print("Exception in forgot_password_request:", e)
        traceback.print_exc()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JSONResponse(status_code=500, content={"error": "Internal server error. Please try again later."})

        return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
            "request": request,
            "detail": "Internal server error. Please try again later.",
            "email": email
        })


@router.post("/forgotpass")
async def reset_password(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    cnfpassword: str = Form(...),
    otp: str = Form(...)
):
    if email not in otp_store or otp_store[email] != otp:
        return HTMLResponse(
            """
            <script>
                alert('Invalid OTP. Please try again.');
                window.history.back(); // Redirects back to the form
            </script>
            """
        )


    if password != cnfpassword:
        return HTMLResponse(
        """
        <script>
            alert('Passwords do not match.');
            window.history.back();
        </script>
        """
    )


    hashed_password = hash_password(password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )

    otp_store.pop(email, None)

    # Return JS alert and redirect to login
    return HTMLResponse(
        """
        <script>
            alert('Your password has been changed successfully.');
            window.location.href = '/Login'; 
        </script>
        """
    )
