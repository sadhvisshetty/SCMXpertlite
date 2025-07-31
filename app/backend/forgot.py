from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from .db import user_collection
from .utils import hash_password
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import os
from dotenv import load_dotenv
from email.message import EmailMessage


load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

FORGOT_PASSWORD_TEMPLATE = "forgotPassword.html"
LOGIN_TEMPLATE = "Login.html"

router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="../frontend/templates")

# In-memory store for OTPs
otp_store = {}

# OTP generator
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

# Send OTP email using Gmail SMTP
def send_otp_email(recipient_email: str, otp: str):
    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg["Subject"] = "Your SCMXpert OTP Code"
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


@router.post("/forgotpass/request")
async def forgot_password_request(request: Request, email: str = Form(...)):

    user = await user_collection.find_one({"email": email})

    if not user:
        return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
            "request": request,
            "detail": "Email not registered."
        })

    otp = generate_otp()
    otp_store[email] = otp
    print(f"Generated OTP for {email}: {otp}")

    send_otp_email(email, otp)

    return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
        "request": request,
        "message": f"OTP sent to {email}.",
        "email": email
    })

# Reset password after OTP verification
@router.post("/forgotpass")
async def reset_password(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    cnfpassword: str = Form(...),
    otp: str = Form(...)
):
    # Validate OTP
    if email not in otp_store or otp_store[email] != otp:
        return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
            "request": request,
            "email": email,
            "detail": "Invalid OTP."
        })

    # Validate password confirmation
    if password != cnfpassword:
        return templates.TemplateResponse(FORGOT_PASSWORD_TEMPLATE, {
            "request": request,
            "email": email,
            "detail": "Passwords do not match."
        })

    # Hash password and update in DB
    hashed_password = hash_password(password)
    await user_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}}
    )

    # Remove OTP after successful reset
    otp_store.pop(email, None)

    # Redirect or show login page with success message
    return templates.TemplateResponse(LOGIN_TEMPLATE, {
        "request": request,
        "message": "Password reset successful. Please log in."
    })
