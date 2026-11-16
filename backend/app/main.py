import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from sqlmodel import Session, SQLModel, select

try:
    from .database import engine
    from .models import (
        Category,
        CategoryCreate,
        CategoryRead,
        Summary,
        Token,
        Transaction,
        TransactionCreate,
        TransactionRead,
        User,
        UserCreate,
        UserRead,
        Wallet,
        WalletCreate,
        WalletRead,
    )
except ImportError:
    from database import engine
    from models import (
        Category,
        CategoryCreate,
        CategoryRead,
        Summary,
        Token,
        Transaction,
        TransactionCreate,
        TransactionRead,
        User,
        UserCreate,
        UserRead,
        Wallet,
        WalletCreate,
        WalletRead,
    )

app = FastAPI(title="Mis Finanzas", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_URL", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-this")
password_hash = PasswordHash.recommended()
bearer = HTTPBearer()


@app.on_event("startup")
def on_startup() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def make_token(user_id: int) -> str:
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Sesión inválida") from error
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


def owned_wallet(session: Session, user_id: int, wallet_id: int) -> Wallet:
    wallet = session.get(Wallet, wallet_id)
    if wallet is None or wallet.user_id != user_id:
        raise HTTPException(status_code=404, detail="Billetera no encontrada")
    return wallet


def owned_category(session: Session, user_id: int, category_id: int) -> Category:
    category = session.get(Category, category_id)
    if category is None or category.user_id != user_id:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@app.get("/")
def read_root():
    return {"status": "ok", "message": "API activa y escuchando"}


@app.post("/auth/register", response_model=UserRead, status_code=201)
def register(data: UserCreate, session: Annotated[Session, Depends(get_session)]):
    if session.exec(select(User).where(User.username == data.username)).first():
        raise HTTPException(status_code=409, detail="Ese usuario ya existe")
    user = User(username=data.username, password_hash=password_hash.hash(data.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    session.add(Wallet(name="Billetera principal", user_id=user.user_id))
    for name in ("Comida", "Transporte", "Estudios", "Otros"):
        session.add(Category(category_name=name, user_id=user.user_id))
    session.commit()
    return user


@app.post("/auth/login", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    user = session.exec(select(User).where(User.username == form.username)).first()
    if user is None or not password_hash.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return Token(access_token=make_token(user.user_id))


@app.get("/auth/me", response_model=UserRead)
def me(user: Annotated[User, Depends(current_user)]):
    return user


@app.get("/wallets", response_model=list[WalletRead])
def list_wallets(user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    return session.exec(select(Wallet).where(Wallet.user_id == user.user_id)).all()


@app.post("/wallets", response_model=WalletRead, status_code=201)
def create_wallet(data: WalletCreate, user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    wallet = Wallet(**data.model_dump(), user_id=user.user_id)
    session.add(wallet)
    session.commit()
    session.refresh(wallet)
    return wallet


@app.get("/categories", response_model=list[CategoryRead])
def list_categories(user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    return session.exec(select(Category).where(Category.user_id == user.user_id)).all()


@app.post("/categories", response_model=CategoryRead, status_code=201)
def create_category(data: CategoryCreate, user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    category = Category(**data.model_dump(), user_id=user.user_id)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@app.get("/transactions", response_model=list[TransactionRead])
def list_transactions(user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    statement = select(Transaction).join(Wallet).where(Wallet.user_id == user.user_id).order_by(Transaction.created_at.desc())
    return session.exec(statement).all()


@app.post("/transactions", response_model=TransactionRead, status_code=201)
def create_transaction(data: TransactionCreate, user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    if data.transaction_type not in {"income", "expense"}:
        raise HTTPException(status_code=422, detail="El tipo debe ser income o expense")
    wallet = owned_wallet(session, user.user_id, data.wallet_id)
    owned_category(session, user.user_id, data.category_id)
    transaction = Transaction(**data.model_dump())
    wallet.balance += data.amount if data.transaction_type == "income" else -data.amount
    session.add(transaction)
    session.add(wallet)
    session.commit()
    session.refresh(transaction)
    return transaction


@app.get("/summary", response_model=Summary)
def summary(user: Annotated[User, Depends(current_user)], session: Annotated[Session, Depends(get_session)]):
    transactions = session.exec(select(Transaction).join(Wallet).where(Wallet.user_id == user.user_id)).all()
    income = sum((item.amount for item in transactions if item.transaction_type == "income"), Decimal("0"))
    expenses = sum((item.amount for item in transactions if item.transaction_type == "expense"), Decimal("0"))
    return Summary(balance=income - expenses, income=income, expenses=expenses)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
