Perfect 👍 here is the **complete, clean, working FastAPI JWT auth project** with:

* ✅ FastAPI
* ✅ SQLAlchemy
* ✅ SQLite
* ✅ Pydantic
* ✅ APIRouter
* ✅ Argon2 password hashing
* ✅ JWT authentication
* ✅ Jinja2 templates
* ✅ Login / Signup / Logout
* ✅ Protected HTML page
* ✅ Redirect to login if not authenticated

---

# 📁 Project Structure

```
fastapi_auth_app/
│
├── main.py
├── database.py
├── models.py
├── schemas.py
├── auth.py
│
├── routers/
│   └── auth_routes.py
│
├── templates/
│   ├── login.html
│   ├── signup.html
│   └── home.html
│
└── requirements.txt
```

---

# 📦 requirements.txt

```
fastapi
uvicorn
sqlalchemy
python-jose
passlib[argon2]
jinja2
python-multipart
```

Install:

```bash
pip install -r requirements.txt
```

---

# 🗄 database.py

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
```

---

# 👤 models.py

```python
from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
```

---

# 📘 schemas.py

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: str | None = None
```

---

# 🔐 auth.py

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

# JWT creation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Protected route dependency
def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")

    if not token:
        return RedirectResponse(url="/login", status_code=302)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return RedirectResponse(url="/login", status_code=302)
    except JWTError:
        return RedirectResponse(url="/login", status_code=302)

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return RedirectResponse(url="/login", status_code=302)

    return user
```

---

# 🚦 routers/auth_routes.py

```python
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import Base, engine
from models import User
from auth import (
    get_db,
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
```

---

# 🚀 main.py

```python
from fastapi import FastAPI
from routers.auth_routes import router

app = FastAPI()

app.include_router(router)
```

---

# 🖥 templates/signup.html

```html
<!DOCTYPE html>
<html>
<body>
<h2>Signup</h2>

<form method="post">
  Username: <input type="text" name="username"><br><br>
  Password: <input type="password" name="password"><br><br>
  <button type="submit">Signup</button>
</form>

{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}

<a href="/login">Already have an account? Login</a>
</body>
</html>
```

---

# 🖥 templates/login.html

```html
<!DOCTYPE html>
<html>
<body>
<h2>Login</h2>

<form method="post">
  Username: <input type="text" name="username"><br><br>
  Password: <input type="password" name="password"><br><br>
  <button type="submit">Login</button>
</form>

{% if error %}
<p style="color:red;">{{ error }}</p>
{% endif %}

<a href="/signup">Don't have an account? Signup</a>
</body>
</html>
```

---

# 🖥 templates/home.html

```html
<!DOCTYPE html>
<html>
<body>
<h2>Welcome {{ user.username }}</h2>

<p>This page is protected. You are logged in.</p>

<a href="/logout">Logout</a>

</body>
</html>
```

---

# ▶️ Run the Project

From project root:

```bash
uvicorn main:app --reload
```

Open:

```
http://127.0.0.1:8000/signup
```

---

# ✅ What You Now Have

* 🔐 Argon2 password hashing
* 🎫 JWT authentication
* 🍪 HTTP-only cookie
* 🛡 Protected route
* 🔓 Login
* 📝 Signup
* 🚪 Logout
* 🔁 Redirect if not authenticated

---
