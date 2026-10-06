#65 introduce sqlalchemy for creating python model classes for Customer,Contract.
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)


# Database connection
DATABASE_URL = (
    "mysql+pymysql://root:root@localhost:3306/telecom"
)

engine = create_engine(DATABASE_URL)


# Base class for ORM models
Base = declarative_base()


# Customer model
class Customer(Base):

    __tablename__ = "customers1"

    customer_id = Column(
        String(20),
        primary_key=True
    )

    gender = Column(
        String(10)
    )

    senior_citizen = Column(
        Integer
    )

    partner = Column(
        Integer
    )

    dependents = Column(
        Integer
    )


# Contract model
class Contract(Base):

    __tablename__ = "dim_contract"

    contract_id = Column(
        Integer,
        primary_key=True
    )

    contract_name = Column(
        String(30)
    )


# Create session
Session = sessionmaker(
    bind=engine
)

session = Session()









# 66. Query one customer
customer = (
    session.query(Customer)
    .filter_by(
        customer_id="7590-VHVEG"
    )
    .first()
)


# Display result
if customer:

    print(
        "Customer ID:",
        customer.customer_id
    )

    print(
        "Gender:",
        customer.gender
    )

    print(
        "Senior Citizen:",
        customer.senior_citizen
    )

    print(
        "Partner:",
        customer.partner
    )

    print(
        "Dependents:",
        customer.dependents
    )

else:

    print("Customer not found")


session.close()