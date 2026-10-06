from sqlalchemy.orm import Session
from sqlalchemy import func


from models import (
    FactCustomerAccount,
    Contract,
    HighRiskCustomer,CustomerMLFeatures
)


def get_churn_summary(db: Session):

    total_customers = (
        db.query(
            func.count(
                FactCustomerAccount.customer_id
            )
        )
        .scalar()
    )

    total_churned = (
        db.query(
            func.count(
                FactCustomerAccount.customer_id
            )
        )
        .filter(
            FactCustomerAccount.churn == 1
        )
        .scalar()
    )



    churn_rate = (
        total_churned / total_customers
        if total_customers > 0
        else 0
    )



    contract_results = (
        db.query(
            Contract.contract_name,
            func.avg(
                FactCustomerAccount.churn
            )
        )
        .join(
            FactCustomerAccount,
            FactCustomerAccount.contract_id
            == Contract.contract_id
        )
        .group_by(
            Contract.contract_name
        )
        .order_by(
            func.avg(
                FactCustomerAccount.churn
            ).desc()
        )
        .all()
    )


    by_contract = [
        {
            "contract_type": contract_name,
            "churn_rate": round(
                float(churn_rate),
                4
            )
        }
        for contract_name, churn_rate
        in contract_results
    ]


    internet_results = (
        db.query(
            FactCustomerAccount.internet_service,
            func.avg(
                FactCustomerAccount.churn
            )
        )
        .group_by(
            FactCustomerAccount.internet_service
        )
        .order_by(
            func.avg(
                FactCustomerAccount.churn
            ).desc()
        )
        .all()
    )


    by_internet_service = [
        {
            "internet_service": internet_service,
            "churn_rate": round(
                float(churn_rate),
                4
            )
        }
        for internet_service, churn_rate
        in internet_results
    ]



    return {
        "total_customers": total_customers,
        "churned": total_churned,
        "churn_rate": round(
            churn_rate,
            4
        ),
        "by_contract": by_contract,
        "by_internet_service": by_internet_service
    }
    
    
    
    
    
    
def get_high_risk_customers(
    db: Session,
    limit: int = 50,
    min_tenure: int | None = None,
    max_tenure: int | None = None
):

    query = db.query(
        HighRiskCustomer
    )

   
    if min_tenure is not None:

        query = query.filter(
            HighRiskCustomer.tenure >= min_tenure
        )

   
    if max_tenure is not None:

        query = query.filter(
            HighRiskCustomer.tenure <= max_tenure
        )

   
    results = (
        query
        .limit(limit)
        .all()
    )

    return [
        {
            "customer_id": customer.customer_id,
            "tenure": customer.tenure,
            "monthly_charges": customer.monthly_charges,
            "contract_type": customer.contract,
            "risk_reason": customer.risk_reason
        }
        for customer in results
    ]
    
    
def get_customer_features(
    db: Session,
    customer_id: str
):

    customer = (
        db.query(CustomerMLFeatures)
        .filter(
            CustomerMLFeatures.customer_id
            == customer_id
        )
        .first()
    )

    return customer