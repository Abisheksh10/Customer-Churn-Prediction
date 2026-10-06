from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey
)

from sqlalchemy.orm import declarative_base


Base = declarative_base()


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


class FactCustomerAccount(Base):

    __tablename__ = "fact_customer_account"

    customer_id = Column(
        String(20),
        ForeignKey(
            "customers1.customer_id"
        ),
        primary_key=True
    )

    tenure = Column(
        Integer
    )

    monthly_charges = Column(
        Float
    )

    total_charges = Column(
        Float
    )

    churn = Column(
        Integer
    )

    contract_id = Column(
        Integer,
        ForeignKey(
            "dim_contract.contract_id"
        )
    )

    payment_id = Column(
        Integer,
        ForeignKey(
            "dim_payment.payment_id"
        )
    )

    internet_service = Column(
        String(20)
    )


class Contract(Base):

    __tablename__ = "dim_contract"

    contract_id = Column(
        Integer,
        primary_key=True
    )

    contract_name = Column(
        String(30)
    )
    
    
    
    
    
class HighRiskCustomer(Base):

    __tablename__ = "v_high_risk_customers"

    customer_id = Column(
        String(20),
        primary_key=True
    )

    tenure = Column(
        Integer
    )

    monthly_charges = Column(
        Float
    )

    contract = Column(
        String(30)
    )

    risk_reason = Column(
        String(200)
    )
    
    

class CustomerMLFeatures(Base):

    __tablename__ = "customer_ml_features"

    customer_id = Column(
        String(20),
        primary_key=True
    )

    tenure = Column(
        Integer
    )

    monthly_charges = Column(
        Float
    )

    total_charges = Column(
        Float
    )

    tenure_bucket = Column(
        String(10)
    )

    high_charge_flag = Column(
        Integer
    )

    service_count = Column(
        Integer
    )

    is_long_term_customer = Column(
        Integer
    )

    has_streaming_bundle = Column(
        Integer
    )

    auto_pay_flag = Column(
        Integer
    )

    churn = Column(
        Integer
    )