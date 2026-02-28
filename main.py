from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from database import engine, SessionLocal
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import models
import schemas
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))   #http://127.0.0.1:8000/static/interactive-register.html
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registred")
    hashed = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        hashed_password=hashed
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
@app.get("/register", response_class=HTMLResponse)
async def register_page():
    with open("static/register-page.html", encoding="utf-8") as f:
        return f.read()
@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open("static/login-page.html", encoding="utf-8") as f:
        return f.read()    
    
@app.post("/token", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/')
def root():
    return {"message":"Habit Tracker with database"}

@app.post("/habits/", response_model=schemas.HabitResponse)
def create_habit(habit: schemas.HabitCreate, db: Session = Depends(get_db),
                 current_user:models.User = Depends(get_current_user)):
    db_habit = models.Habit(
        title=habit.title,
        description=habit.description,
        user_id=current_user.id
    )
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

@app.get("/habits/", response_model=list[schemas.HabitResponse])
def read_habits(skip: int = 0,
                limit: int = 10,
                sort_by: str = "created",
                order: str = "desc",
                db: Session = Depends(get_db),
                filter_by: str = "all",
                current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Habit).filter(models.Habit.user_id == current_user.id)
    if filter_by == "active":
        query = query.filter(models.Habit.established == False)
    elif filter_by == "established":
        query = query.filter(models.Habit.established == True)
    if sort_by == "title":
        if order == "asc":
            query = query.order_by(models.Habit.title.asc())
        else:
            query = query.order_by(models.Habit.title.desc())
    elif sort_by == "streak":
        if order == "asc":
            query = query.order_by(models.Habit.streak.asc())
        else:
            query = query.order_by(models.Habit.streak.desc())
    else:
        if order == "asc":
            query = query.order_by(models.Habit.id.asc())
        else:
            query = query.order_by(models.Habit.id.desc())
    habits = query.offset(skip).limit(limit).all()  
    return habits

@app.get("/habits/{habit_id}", response_model=schemas.HabitResponse)
def read_habit(habit_id: int,
            db: Session = Depends(get_db),
            current_user: models.User = Depends(get_current_user)):
    db_habit = db.query(models.Habit)\
           .filter(models.Habit.id == habit_id,
                   models.Habit.user_id == current_user.id)\
            .first()
    if db_habit is None:
        raise HTTPException(status_code=404,detail="Habit not found")
    return db_habit                
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    return db_habit           
    
@app.patch("/habits/{habit_id}/complete", response_model=schemas.HabitResponse)
def complete_habit(habit_id: int, 
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    db_habit = db.query(models.Habit)\
                 .filter(models.Habit.id == habit_id,
                         models.Habit.user_id == current_user.id)\
                 .first()
    if db_habit is None:
        raise HTTPException(status_code=404, detail="Habit not found")
    db_habit.completed = not db_habit.completed
    db.commit()
    db.refresh(db_habit)
    return db_habit
@app.delete("/habits/{habit_id}")
def delete_habit(habit_id: int,
                db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    habit = db.query(models.Habit)\
            .filter(models.Habit.id == habit_id,
                    models.Habit.user_id == current_user.id)\
            .first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    return {"message": "Habit deleted successfully"}
@app.post("/habits/{habit_id}/log", response_model=schemas.HabitResponse)
def log_habit(habit_id: int,
              db: Session = Depends(get_db),
              current_user: models.User = Depends(get_current_user)):
        habit = db.query(models.Habit)\
                .filter(models.Habit.id == habit_id,
                        models.Habit.user_id == current_user.id)\
                .first()
        if not habit:
            raise HTTPException(status_code=404, detail="Habit not found")
        today = datetime.now()
        existing_log = db.query(models.HabitLog)\
                        .filter(models.HabitLog.habit_id == habit_id,
                                models.HabitLog.date >= today.replace(hour=0, minute=0,
                                                                      second=0))\
                                                                      .first()
        if existing_log:
            raise HTTPException(status_code=400, detail="Already logged today")
        log = models.HabitLog(habit_id=habit_id)
        db.add(log)

        if habit.last_log_date:
            last_date = habit.last_log_date.date()
            today_date = datetime.now().date()
            if last_date == today_date - timedelta(days=1):
                habit.streak += 1
            elif last_date == today_date:
                pass
            else:
                habit.streak = 1
        else:
            habit.streak = 1
        habit.last_log_date=today
        if habit.streak >= 40:
            habit.established = True
        db.commit()
        db.refresh(habit)
        return habit

