from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, min_length=3, max_length=40)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=100)


class User(UserBase, table=True):
    __tablename__ = "user"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    wallets: list["Wallet"] = Relationship(back_populates="user")
    categories: list["Category"] = Relationship(back_populates="user")


class UserRead(UserBase):
    user_id: int


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class WalletBase(SQLModel):
    name: str = Field(min_length=1, max_length=50)
    balance: Decimal = Field(default=Decimal("0"), max_digits=12, decimal_places=2)


class WalletCreate(WalletBase):
    pass


class Wallet(WalletBase, table=True):
    __tablename__ = "wallet"

    wallet_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates="wallets")
    transactions: list["Transaction"] = Relationship(back_populates="wallet")


class WalletRead(WalletBase):
    wallet_id: int
    created_at: datetime


class CategoryBase(SQLModel):
    category_name: str = Field(min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase, table=True):
    __tablename__ = "category"

    category_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id")
    user: Optional[User] = Relationship(back_populates="categories")
    transactions: list["Transaction"] = Relationship(back_populates="category")


class CategoryRead(CategoryBase):
    category_id: int


class TransactionBase(SQLModel):
    wallet_id: int = Field(foreign_key="wallet.wallet_id")
    category_id: int = Field(foreign_key="category.category_id")
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    payment_method: Optional[str] = Field(default=None, max_length=40)
    transaction_type: str


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase, table=True):
    __tablename__ = "transaction"

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    wallet: Optional[Wallet] = Relationship(back_populates="transactions")
    category: Optional[Category] = Relationship(back_populates="transactions")


class TransactionRead(TransactionBase):
    transaction_id: int
    created_at: datetime


class Summary(SQLModel):
    balance: Decimal
    income: Decimal
    expenses: Decimal
