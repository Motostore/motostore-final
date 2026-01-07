from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship
from app.core.database import Base

# ===================== CATEGORÍAS ===================== #

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category")


# ===================== PRODUCTOS ===================== #

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="products")


# ===================== MARKETING ===================== #

class Marketing(Base):
    __tablename__ = "marketing"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===================== RECHARGES ===================== #

class Recharge(Base):
    __tablename__ = "recharges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===================== LICENSES ===================== #

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    client = Column(String(150), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LicenseProvider(Base):
    __tablename__ = "license_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===================== USUARIOS (MODIFICADO) ===================== #

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)

    password = Column(String(255), nullable=True) 
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(30), nullable=False, default="CLIENT")
    is_superuser = Column(Boolean, default=False)
    balance = Column(Float, default=0.0)

    is_active = Column(Boolean, nullable=True, default=True)
    full_name = Column(String(255), nullable=True)
    cedula = Column(String(30), nullable=True)
    telefono = Column(String(30), nullable=True)

    # 🔥 NUEVO CAMPO: JERARQUÍA 🔥
    # Esto permite saber quién es el "Jefe" de este usuario
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relación para acceder a los hijos (clientes) fácilmente
    children = relationship("User", backref="parent", remote_side=[id])

    # Relaciones existentes
    wallet_transactions = relationship("WalletTransaction", backref="user", lazy="select")
    orders = relationship("Order", backref="user", lazy="select")


# ===================== CLIENTES ===================== #

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    document_id = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    active = Column(Boolean, default=True)


# ===================== MÉTODOS DE PAGO ===================== #

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    type = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=True)
    bank_code = Column(String(20), nullable=True)
    account_number = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    id_number = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


# ===================== HISTORIAL WALLET ===================== #

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(String(20), default="DEPOSIT")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===================== ORDERS (VENTAS) ===================== #

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    total_amount = Column(Float, nullable=False)
    cost_amount = Column(Float, default=0.0)
    
    status = Column(String(20), default="completed") 
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ===================== PAYMENTS REPORT ===================== #

class PaymentReport(Base):
    __tablename__ = "payment_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(String(20), default="PENDING")
    proof_url = Column(String(500), nullable=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    rejected_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)


# ===================== HELPERS ===================== #

def create_default_superuser(db):
    from sqlalchemy import select

    try:
        total = db.query(User).count()
        if total > 0:
            return
    except:
        return

    su = User(
        name="Dueño MotoStore",
        email="admin@motostore.com",
        username="admin_moto",
        password="13101310",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6qVictorJ0hN9qJ",
        is_superuser=True,
        role="SUPERUSER",
        is_active=True,
        balance=1000000.0,
        parent_id=None # El Superuser no tiene jefe
    )
    db.add(su)
    db.commit()













