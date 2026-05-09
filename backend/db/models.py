from sqlalchemy import Column, String, Integer, Float, Date, Boolean
from db.connection import Base


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    client_id = Column(String, nullable=False, index=True)
    order_date = Column(Date, nullable=False, index=True)
    delivery_date = Column(Date, nullable=True)
    carrier = Column(String, nullable=False, index=True)
    origin_city = Column(String, nullable=False)
    destination_city = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    product_category = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price_usd = Column(Float, nullable=False)
    order_value_usd = Column(Float, nullable=False)
    is_promo = Column(Boolean, nullable=False, default=False)
    promo_discount_pct = Column(Integer, nullable=False, default=0)
    region = Column(String, nullable=False, index=True)
    warehouse = Column(String, nullable=False)
