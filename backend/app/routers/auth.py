"""
Auth router — signup/login via Supabase Auth.

Signup: Uses admin client with email_confirm=True to bypass email verification in development.
        In production, set ENV=production and email confirmation will be required.
Login:  Uses regular auth client.
"""
import logging
from fastapi import APIRouter, HTTPException, status
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse
from app.supabase_client import get_supabase, get_supabase_admin
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest):
    """
    Create a new account.
    In development: auto-confirms email so the user can log in immediately.
    In production: sends confirmation email (set ENV=production in .env).
    """
    try:
        if settings.env == "development":
            # Admin client → creates and confirms user immediately — no email needed
            admin = get_supabase_admin()
            result = admin.auth.admin.create_user({
                "email": body.email,
                "password": body.password,
                "email_confirm": True,
            })
            user = result.user
            if not user:
                raise HTTPException(status_code=400, detail="Signup failed.")

            # Admin create_user doesn't return a session — sign in immediately to get token
            supabase = get_supabase()
            session_result = supabase.auth.sign_in_with_password(
                {"email": body.email, "password": body.password}
            )
            session = session_result.session
            if not session:
                raise HTTPException(status_code=400, detail="Signup succeeded but login failed.")

            return AuthResponse(
                access_token=session.access_token,
                user_id=user.id,
                email=user.email,
            )
        else:
            # Production: standard flow with email confirmation
            supabase = get_supabase()
            response = supabase.auth.sign_up({"email": body.email, "password": body.password})
            if not response.user:
                raise HTTPException(status_code=400, detail="Signup failed.")
            return AuthResponse(
                access_token="",  # Not issued until email confirmed
                user_id=response.user.id,
                email=response.user.email,
                message="Please check your email to confirm your account.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Log in with email and password. Returns a JWT access token."""
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )
        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
