from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from database import SessionLocal, File as DBFile, User
import aiofiles
import os
import csv

app = FastAPI()
templates = Jinja2Templates(directory="templates")

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'csv'}

@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/upload/')
async def upload(request: Request, file_input: UploadFile = File(...)):
   
    file_name, file_extension = os.path.splitext(file_input.filename)
    file_extension = file_extension[1:].lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

   
    file_content = await file_input.read()

 
    file_path = os.path.join(UPLOADS_DIR, file_input.filename)

    
    async with aiofiles.open(file_path, 'wb') as file:
        await file.write(file_content)

    db = SessionLocal()

    try:
       
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for row in csv_reader:
                
                name = row.get('name')
                age = int(row.get('age')) if row.get('age') else None

               
                user = User(name=name, age=age)
                db.add(user)

        db.commit()

       
        db_file = DBFile(file_name=file_input.filename, file_path=file_path)
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    finally:
        db.close()

    return {"message": "File uploaded successfully", "file_id": db_file.id}