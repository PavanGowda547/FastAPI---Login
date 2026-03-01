from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import User
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

Base.metadata.create_all(bind=engine)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ---------------- SIGNUP ----------------
@router.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "User already exists"},
        )

    new_user = User(
        username=username,
        hashed_password=hash_password(password),
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=302)

# ---------------- LOGIN ----------------
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials"},
        )

    token = create_access_token({"sub": user.username})

    response = RedirectResponse(url="/home", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
    )
    return response

# ---------------- HOME (PROTECTED) ----------------
@router.get("/home", response_class=HTMLResponse)
def home(
    request: Request,
    user: User = Depends(get_current_user),
):
    # If get_current_user returned RedirectResponse
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user},
    )

# ---------------- LOGOUT ----------------
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response