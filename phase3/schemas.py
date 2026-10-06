from pydantic import BaseModel,field_validator


class CustomerResponse(BaseModel):

    customer_id: str
    tenure: int
    contract_type: str
    internet_service: str
    monthly_charges: float
    churn: int
    
    
    
class HighRiskCustomerResponse(BaseModel):

    customer_id: str
    tenure: int
    monthly_charges: float
    contract_type: str
    risk_reason: str


class CustomerFeatures(BaseModel):

    service_count: int
    tenure_bucket: str
    high_charge_flag: int
    is_long_term_customer: int
    has_streaming_bundle: int
    auto_pay_flag: int
    monthly_charges: float
    total_charges: float
    
    
class ChurnPredictionRequest(BaseModel):
    tenure: int
    monthly_charges: float
    contract_type: str
    service_count: int

    @field_validator("tenure")
    @classmethod
    def validate_tenure(cls, value):
        if value < 0:
            raise ValueError("tenure must be greater than or equal to 0")

        if value > 100:
            raise ValueError("tenure must be less than or equal to 100")

        return value

    @field_validator("monthly_charges")
    @classmethod
    def validate_monthly_charges(cls, value):
        if value <= 0:
            raise ValueError("monthly_charges must be greater than 0")

        return value
    

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
