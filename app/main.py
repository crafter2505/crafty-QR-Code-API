import os
import requests
import logging
import secrets
from fastapi import FastAPI, Query, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import qrcode
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from app.database import (
    init_db, create_user, create_api_key, get_user_by_email, 
    get_api_key_by_user_id, get_user_by_token, verify_user
)
from app.models import RegisterRequest, RegisterResponse
from app.auth import verify_api_key, PLAN_LIMITS

load_dotenv()
init_db()
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
VERIFY_BASE_URL = os.getenv("VERIFY_BASE_URL", "http://localhost:8000")
def send_verification_email(email: str, token: str):
    link = f"{VERIFY_BASE_URL}/verify?token={token}"
    
    # Brand colors
    primary_color = "#7b2ffc"
    secondary_color = "#00d4ff"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
    </head>
    <body style="margin:0; padding:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f0f1a;">
        <table align="center" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #1a1a2e; border-radius: 16px; border: 1px solid #2a2a4a; padding: 40px;">
            <tr>
                <td align="center" style="padding-bottom: 24px;">
                    <h1 style="font-size: 28px; font-weight: 700; background: linear-gradient(135deg, {secondary_color}, {primary_color}); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                        🔲 QR API
                    </h1>
                </td>
            </tr>
            <tr>
                <td style="color: #e0e0e0; font-size: 16px; line-height: 1.6; text-align: center; padding-bottom: 16px;">
                    <h2 style="color: #ffffff; font-size: 22px; margin-bottom: 8px;">Welcome to QR API!</h2>
                    <p style="margin: 0;">Thanks for signing up. Please verify your email address to start generating QR codes instantly.</p>
                </td>
            </tr>
            <tr>
                <td align="center" style="padding: 24px 0;">
                    <a href="{link}" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, {secondary_color}, {primary_color}); color: #ffffff; text-decoration: none; border-radius: 10px; font-size: 16px; font-weight: 600; transition: opacity 0.2s;">
                        🔓 Verify Email
                    </a>
                </td>
            </tr>
            <tr>
                <td style="color: #8888aa; font-size: 14px; line-height: 1.6; text-align: center; padding-bottom: 16px;">
                    <p style="margin: 0;">This link will expire in <strong>24 hours</strong>.</p>
                    <p style="margin: 8px 0 0 0;">If you didn't create an account, you can safely ignore this email.</p>
                </td>
            </tr>
            <tr>
                <td style="border-top: 1px solid #2a2a4a; padding-top: 24px; color: #555577; font-size: 12px; text-align: center;">
                    <p style="margin: 0;">© 2026 QR API. Built with ❤️</p>
                    <p style="margin: 4px 0 0 0;">
                        <a href="{VERIFY_BASE_URL}" style="color: #7b2ffc; text-decoration: none;">Home</a> &bull; 
                        <a href="{VERIFY_BASE_URL}/docs" style="color: #7b2ffc; text-decoration: none;">API Docs</a>
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "QR API <onboarding@resend.dev>",
                "to": [email],
                "subject": "🎯 Welcome to QR API — Verify Your Account",
                "html": html_content
            }
        )
        
        if response.status_code == 200:
            logger.info(f"Verification email sent to {email}")
        else:
            logger.error(f"Resend error: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

app = FastAPI(
    title="QR code Generator API",
    description="Generate QR codes from URLs or text",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def validate_url_or_text(data: str):
    if len(data) > 512:
        raise HTTPException(status_code=400, detail="Input too long (max 512 characters)")
    data = data.strip()
    if not data:
        raise HTTPException(status_code=400, detail="Input cannot be empty")
    return data

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Routes ---

@app.get("/")
def root():
    return {"message": "QR Code Generator API", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/verify")
def verify_email(token: str):
    """Verify a user's email address using the verification token"""
    user = get_user_by_token(token)
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    user_id = user[0]
    verify_user(user_id)
    
    return {"message": "Email verified successfully! You can now generate API keys."}

@app.post("/register", response_model=RegisterResponse)
def register_user(request: RegisterRequest):
    existing_user = get_user_by_email(request.email)

    if existing_user:
        user_id = existing_user[0]
        is_verified = existing_user[2]
        
        if not is_verified:
            # Resend verification email
            token = existing_user[3]
            send_verification_email(request.email, token)
            raise HTTPException(
                status_code=400, 
                detail="Email not verified. A new verification email has been sent."
            )
        
        existing_key = get_api_key_by_user_id(user_id)
        if existing_key:
            return RegisterResponse(
                api_key=existing_key["key"],
                plan=existing_key["plan"],
                expires_in_days=30,
                message="Existing API key retrieved!"
            )
        else:
            api_key = create_api_key(user_id, request.plan)
    else:
        # New user: create with verification token
        verification_token = secrets.token_urlsafe(32)
        user_id = create_user(request.email, verification_token)
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Registration Failed!")
        
        # Send verification email
        send_verification_email(request.email, verification_token)
        
        # Don't create API key yet — wait for verification
        raise HTTPException(
            status_code=202,
            detail="Registration successful! Please check your email to verify your account."
        )

    return RegisterResponse(
        api_key=api_key,
        plan=request.plan,
        expires_in_days=30,
        message="Registration Successful!"
    )
    
@app.get("/generate")
@limiter.limit("5/minute")
def generate_QR(
    request: Request,
    data: str = Query(..., description="Text or URL to encode"),
    size: int = Query(10, description="QR code size (1-20)", ge=1, le=20),
    key_data: dict = Depends(verify_api_key)
):
    try:
        data = validate_url_or_text(data)
        logger.info(f"QR generated for: {data[:50]}... by IP: {request.client.host}")
        qr = qrcode.QRCode(version=1, box_size=size, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        return StreamingResponse(buffered, media_type="image/png")
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})