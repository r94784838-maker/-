# main.py
from fastapi import FastAPI, Depends, Form, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
from database import get_db
from security import hash_password, verify_password, create_access_token, decode_access_token

app = FastAPI(title="Conference Registration System")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- СЛУЖБОВА ФУНКЦІЯ ПЕРЕВІРКИ КУК ---
def get_current_user_from_cookie(request: Request):
    token_cookie = request.cookies.get("access_token")
    if not token_cookie:
        return None
    try:
        scheme, token = token_cookie.split(" ")
        if scheme.lower() != "bearer":
            return None
        payload = decode_access_token(token)
        return payload  # Повертає {"sub": email, "auth_id": id}
    except Exception:
        return None


# --- ГОЛОВНА СТОРІНКА ---
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    user_payload = get_current_user_from_cookie(request)
    current_user = user_payload.get("sub") if user_payload else None
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"current_user": current_user}
    )


# --- СТОРІНКА РЕЄСТРАЦІЇ (GET) ---
@app.get("/register-page", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    genders = db.query(models.Gender).all()
    nationalities = db.query(models.Nationality).all()
    return templates.TemplateResponse(
        request=request, 
        name="register.html", 
        context={"genders": genders, "nationalities": nationalities}
    )


# --- ОБРОБКА РЕЄСТРАЦІЇ (POST) ---
@app.post("/register")
def register_user(
    request: Request,
    first_name: str = Form(...),
    second_name: str = Form(...),
    date_of_birth: str = Form(...),
    id_gender: int = Form(...),
    id_nation: int = Form(...),
    organization_name: str = Form(...),
    job_title: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    genders = db.query(models.Gender).all()
    nationalities = db.query(models.Nationality).all()
    context_data = {"genders": genders, "nationalities": nationalities}

    # 1. Валідація довжини пароля
    if len(password) < 6:
        context_data["error"] = "Пароль надто короткий! Мінімальна довжина — 6 символів."
        return templates.TemplateResponse(request=request, name="register.html", context=context_data)

    # 2. Валідація збігу паролів
    if password != confirm_password:
        context_data["error"] = "Паролі не збігаються! Перевірте введення."
        return templates.TemplateResponse(request=request, name="register.html", context=context_data)

    # 3. Перевірка унікальності Email
    existing_auth = db.query(models.AuthInfo).filter(models.AuthInfo.email == email).first()
    if existing_auth:
        context_data["error"] = "Користувач з таким Email вже зареєстрований."
        return templates.TemplateResponse(request=request, name="register.html", context=context_data)
    
    # 4. Збереження в базу
    hashed_pwd = hash_password(password)
    db_auth = models.AuthInfo(email=email, password=hashed_pwd)
    db.add(db_auth)
    db.commit()
    db.refresh(db_auth)
    
    db_personal = models.PersonalInfo(first_name=first_name, second_name=second_name, date_of_birth=date_of_birth)
    db.add(db_personal)
    db.commit()
    db.refresh(db_personal)
    
    db_person = models.Person(
        id_auth=db_auth.id_auth,
        id_personal=db_personal.id_personal,
        id_gender=id_gender,
        id_nation=id_nation,
        organization_name=organization_name,
        job_title=job_title
    )
    db.add(db_person)
    db.commit()
    
    return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)


# --- СТОРІНКА ВХОДУ (GET) ---
@app.get("/login-page", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


# --- ОБРОБКА ВХОДУ (POST) ---
@app.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_auth = db.query(models.AuthInfo).filter(models.AuthInfo.email == email).first()
    
    if not db_auth or not verify_password(password, db_auth.password):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Невірний email або пароль. Спробуйте ще раз!"}
        )
    
    access_token = create_access_token(data={"sub": db_auth.email, "auth_id": db_auth.id_auth})
    response = RedirectResponse(url="/participants", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


# --- ВИХІД З АКАУНТУ ---
@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


# --- СТОРІНКА УЧАСНИКІВ (ЗАХИЩЕНА) ---
@app.get("/participants", response_class=HTMLResponse)
def participants_list(request: Request, db: Session = Depends(get_db)):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)
    
    current_user = user_payload.get("sub")
    query_results = db.query(models.Person, models.PersonalInfo, models.AuthInfo)\
        .join(models.PersonalInfo, models.Person.id_personal == models.PersonalInfo.id_personal)\
        .join(models.AuthInfo, models.Person.id_auth == models.AuthInfo.id_auth)\
        .all()
    
    return templates.TemplateResponse(
        request=request,
        name="participants.html",
        context={"participants": query_results, "current_user": current_user}
    )


# --- СТОРІНКА РЕДАГУВАННЯ (ЗАХИЩЕНА, GET) ---
@app.get("/edit-page", response_class=HTMLResponse)
def edit_page(request: Request, db: Session = Depends(get_db)):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)
    
    auth_id = user_payload.get("auth_id")
    person = db.query(models.Person, models.PersonalInfo, models.AuthInfo)\
        .join(models.PersonalInfo, models.Person.id_personal == models.PersonalInfo.id_personal)\
        .join(models.AuthInfo, models.Person.id_auth == models.AuthInfo.id_auth)\
        .filter(models.Person.id_auth == auth_id).first()
        
    genders = db.query(models.Gender).all()
    nationalities = db.query(models.Nationality).all()
    
    return templates.TemplateResponse(
        request=request,
        name="edit.html",
        context={"person": person, "genders": genders, "nationalities": nationalities, "current_user": user_payload.get("sub")}
    )


# --- ОБРОБКА РЕДАГУВАННЯ (ЗАХИЩЕНА, POST) ---
@app.post("/edit")
def edit_user(
    request: Request,
    first_name: str = Form(...),
    second_name: str = Form(...),
    date_of_birth: str = Form(...),
    id_gender: int = Form(...),
    id_nation: int = Form(...),
    organization_name: str = Form(...),
    job_title: str = Form(...),
    db: Session = Depends(get_db)
):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/login-page", status_code=status.HTTP_303_SEE_OTHER)
        
    auth_id = user_payload.get("auth_id")
    person = db.query(models.Person).filter(models.Person.id_auth == auth_id).first()
    personal_info = db.query(models.PersonalInfo).filter(models.PersonalInfo.id_personal == person.id_personal).first()
    
    personal_info.first_name = first_name
    personal_info.second_name = second_name
    personal_info.date_of_birth = date_of_birth
    
    person.id_gender = id_gender
    person.id_nation = id_nation
    person.organization_name = organization_name
    person.job_title = job_title
    
    db.commit()
    return RedirectResponse(url="/participants", status_code=status.HTTP_303_SEE_OTHER)