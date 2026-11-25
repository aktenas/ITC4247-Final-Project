from typing import List
from fastapi import Depends, FastAPI, HTTPException, Path, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import engine, get_db

# Automatically create MySQL tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Corporate Expense & Procurement REST API",
    description="ITC 4247 Secure Software Development REST Web Service",
    version="1.0.0",
)


# Global exception handler so unhandled crashes never leak stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."},
    )


# --- AUTHENTICATION ENDPOINTS ---

@app.post("/api/auth/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username is already taken")

    new_user = models.User(
        username=user_data.username,
        password_hash=auth.hash_password(user_data.password),
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not user or not auth.verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = auth.create_access_token(user_id=user.id, role=user.role)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/users/me", response_model=schemas.UserOut)
def read_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --- EXPENSE RESOURCE ENDPOINTS ---

@app.post("/api/expenses", response_model=schemas.ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: schemas.ExpenseCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    new_expense = models.Expense(
        owner_id=current_user.id,
        amount=expense_data.amount,
        category=expense_data.category,
        description=expense_data.description,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@app.get("/api/expenses", response_model=List[schemas.ExpenseOut])
def list_expenses(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    # Managers view all company expenses; employees only view their own
    if current_user.role == "manager":
        return db.query(models.Expense).all()
    return db.query(models.Expense).filter(models.Expense.owner_id == current_user.id).all()


@app.get("/api/expenses/{expense_id}", response_model=schemas.ExpenseOut)
def get_expense_by_id(
    expense_id: int = Path(..., gt=0, description="Positive integer ID"),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense record not found")

    # Prevent IDOR (Insecure Direct Object Reference)
    if current_user.role != "manager" and expense.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this expense")

    return expense


@app.patch("/api/expenses/{expense_id}/status", response_model=schemas.ExpenseOut)
def update_expense_status(
    status_update: schemas.ExpenseStatusUpdate,
    expense_id: int = Path(..., gt=0),
    manager: models.User = Depends(auth.require_manager),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense record not found")

    expense.status = status_update.status
    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/api/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int = Path(..., gt=0),
    manager: models.User = Depends(auth.require_manager),
    db: Session = Depends(get_db),
):
    expense = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense record not found")

    db.delete(expense)
    db.commit()
    return None