from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from . import models, schemas, auth, utils
from .database import get_db, engine
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="URL Shortener API",
    description="A modern URL shortener with JWT authentication, analytics, and custom short codes",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def read_root():
    """Serve the web interface"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            content = f.read()
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=content)
    return {"message": "Welcome to URL Shortener API. Visit /docs for API documentation."}

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = auth.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = auth.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    return auth.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/urls/", response_model=schemas.URLResponse)
def create_short_url(
    url: schemas.URLCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if url.custom_code:
        if not utils.is_valid_short_code(url.custom_code):
            raise HTTPException(status_code=400, detail="Invalid custom code format")
        existing_url = db.query(models.URL).filter(models.URL.short_code == url.custom_code).first()
        if existing_url:
            raise HTTPException(status_code=400, detail="Custom code already in use")
        short_code = url.custom_code
    else:
        short_code = utils.generate_short_code()
        while db.query(models.URL).filter(models.URL.short_code == short_code).first():
            short_code = utils.generate_short_code()
    
    expires_at = None
    if url.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=url.expires_in_days)
    
    db_url = models.URL(
        original_url=str(url.original_url),
        short_code=short_code,
        expires_at=expires_at,
        owner_id=current_user.id
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    base_url = "http://localhost:8000"
    db_url.short_url = f"{base_url}/{short_code}"
    
    return db_url

@app.get("/urls/", response_model=List[schemas.URLResponse])
def read_urls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    urls = db.query(models.URL).filter(models.URL.owner_id == current_user.id).offset(skip).limit(limit).all()
    for url in urls:
        url.short_url = f"http://localhost:8000/{url.short_code}"
    return urls

@app.get("/urls/{url_id}", response_model=schemas.URLResponse)
def read_url(
    url_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_url = db.query(models.URL).filter(models.URL.id == url_id, models.URL.owner_id == current_user.id).first()
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    db_url.short_url = f"http://localhost:8000/{db_url.short_code}"
    return db_url

@app.delete("/urls/{url_id}")
def delete_url(
    url_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_url = db.query(models.URL).filter(models.URL.id == url_id, models.URL.owner_id == current_user.id).first()
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    db_url.is_active = False
    db.commit()
    return {"message": "URL deactivated"}

@app.get("/{short_code}")
def redirect_to_url(short_code: str, request: Request, db: Session = Depends(get_db)):
    db_url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if db_url is None or not db_url.is_active:
        raise HTTPException(status_code=404, detail="URL not found")
    
    if db_url.expires_at and db_url.expires_at < datetime.utcnow():
        db_url.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="URL expired")
    
    db_url.click_count += 1
    
    click = models.Click(
        url_id=db_url.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer")
    )
    db.add(click)
    db.commit()
    
    return RedirectResponse(url=db_url.original_url)

@app.get("/urls/{url_id}/stats", response_model=schemas.URLStats)
def get_url_stats(
    url_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_url = db.query(models.URL).filter(models.URL.id == url_id, models.URL.owner_id == current_user.id).first()
    if db_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    
    clicks = db.query(models.Click).filter(models.Click.url_id == url_id).all()
    
    unique_ips = set(click.ip_address for click in clicks if click.ip_address)
    
    clicks_by_date = {}
    for click in clicks:
        date_str = click.timestamp.strftime("%Y-%m-%d")
        clicks_by_date[date_str] = clicks_by_date.get(date_str, 0) + 1
    
    referer_count = {}
    for click in clicks:
        if click.referer:
            referer_count[click.referer] = referer_count.get(click.referer, 0) + 1
    
    top_referrers = [{"referer": k, "count": v} for k, v in sorted(referer_count.items(), key=lambda x: x[1], reverse=True)[:10]]
    
    recent_clicks = [{"timestamp": click.timestamp, "ip_address": click.ip_address, "user_agent": click.user_agent} for click in clicks[-10:]]
    
    return schemas.URLStats(
        total_clicks=db_url.click_count,
        unique_visitors=len(unique_ips),
        clicks_by_date=clicks_by_date,
        top_referrers=top_referrers,
        recent_clicks=recent_clicks
    )
