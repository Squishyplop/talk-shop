from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import Float, Integer, String, create_engine, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


# =====================================================================================
#                                     DATA MODEL
# =====================================================================================
@dataclass
class Product:
    name: str
    price: float
    stock: int


example_data: list[Product] = [
    Product(name="Monorail", price=1449.99, stock=30),
    Product(name="Hewlett Packard", price=1849.99, stock=23),
    Product(name="COMPAQ", price=2399.99, stock=8),
]


# =====================================================================================
#                                  DATABASE INTERFACE
# =====================================================================================
class DatabaseModel(DeclarativeBase):
    pass


class ProductModel(DatabaseModel):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    price: Mapped[float] = mapped_column(Float(), nullable=False)
    stock: Mapped[int] = mapped_column(Integer(), nullable=False)

    @staticmethod
    def to_model(product: Product) -> ProductModel:
        return ProductModel(name=product.name, price=product.price, stock=product.stock)

    def from_model(self) -> Product:
        return Product(name=self.name, price=self.price, stock=self.stock)


class Database:
    def __init__(self, db_url: str = "sqlite:///shop.db") -> None:
        self.engine: Engine = create_engine(db_url)
        DatabaseModel.metadata.create_all(self.engine)

    def add_product(self, name: str, price: float, stock: int) -> bool:
        """Dodaje nowy produkt do bazy danych."""
        try:
            with Session(self.engine) as session:
                existing = session.scalars(
                    select(ProductModel).where(ProductModel.name.ilike(name.strip()))
                ).first()
                if existing:
                    print(f"Błąd: Produkt '{name}' już istnieje w bazie.")
                    return False

                new_product = ProductModel(name=name.strip(), price=price, stock=stock)
                session.add(new_product)
                session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Błąd podczas dodawania produktu: {e}")
            return False

    def get_product(self, name: str) -> Product | None:
        """Pobiera produkt po nazwie (niezależnie od wielkości liter)."""
        try:
            with Session(self.engine) as session:
                prod_model = session.scalars(
                    select(ProductModel).where(ProductModel.name.ilike(name.strip()))
                ).first()
                if prod_model:
                    return prod_model.from_model()
                return None
        except SQLAlchemyError as e:
            print(f"Błąd bazy danych przy wyszukiwaniu: {e}")
            return None

    def update_product(
        self, name: str, price: float | None = None, stock: int | None = None
    ) -> bool:
        """Aktualizuje cenę lub/i stan magazynowy produktu."""
        try:
            with Session(self.engine) as session:
                prod_model = session.scalars(
                    select(ProductModel).where(ProductModel.name.ilike(name.strip()))
                ).first()
                if not prod_model:
                    print(f"Błąd: Produkt '{name}' nie istnieje w bazie.")
                    return False

                if price is not None:
                    prod_model.price = price
                if stock is not None:
                    prod_model.stock = stock

                session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Błąd podczas edycji produktu: {e}")
            return False

    def delete_product(self, name: str) -> bool:
        """Usuwa produkt z bazy danych."""
        try:
            with Session(self.engine) as session:
                prod_model = session.scalars(
                    select(ProductModel).where(ProductModel.name.ilike(name.strip()))
                ).first()
                if not prod_model:
                    print(f"Błąd: Produkt '{name}' nie istnieje.")
                    return False

                session.delete(prod_model)
                session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Błąd podczas usuwania produktu: {e}")
            return False

    def get_all_products(self) -> list[Product]:
        """Zwraca listę wszystkich produktów."""
        try:
            with Session(self.engine) as session:
                products: Sequence[ProductModel] = session.scalars(select(ProductModel)).all()
                return [p.from_model() for p in products]
        except SQLAlchemyError as e:
            print(f"Błąd podczas pobierania listy produktów: {e}")
            return []

    def clear_database(self) -> bool:
        """Czyszczenie całej bazy danych."""
        try:
            with Session(self.engine) as session:
                session.query(ProductModel).delete(synchronize_session="fetch")
                session.commit()
                return True
        except SQLAlchemyError as e:
            print(f"Błąd podczas czyszczenia bazy danych: {e}")
            return False

    def seed_example_data(self) -> None:
        """Wypełnia bazę początkowymi danymi, jeśli jest pusta."""
        if not self.get_all_products():
            for p in example_data:
                self.add_product(p.name, p.price, p.stock)