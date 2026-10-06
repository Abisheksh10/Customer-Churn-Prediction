import os
import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    Request
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from dotenv import load_dotenv
from models import (
    Customer,
    FactCustomerAccount,
    Contract
)

from schemas import (CustomerResponse,HighRiskCustomerResponse,CustomerFeatures,ChurnPredictionRequest,ErrorResponse)
from services import (get_churn_summary,get_high_risk_customers,get_customer_features)
from predict import predict_churn


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI
# --------------------------------------------------

app = FastAPI(
    title="Customer API"
)


# --------------------------------------------------
# API Key
# --------------------------------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")




app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_api_key(
    x_api_key: str | None
):

    if not API_KEY:

        logger.error(
            "API_KEY environment variable is not configured"
        )

        raise HTTPException(
            status_code=500,
            detail="API key configuration is missing"
        )

    if x_api_key != API_KEY:

        logger.warning(
            "Unauthorized request: invalid or missing API key"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )


# --------------------------------------------------
# 404 Handler
# --------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(
    request: Request,
    exc
):

    logger.warning(
        "%s %s -> 404",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Resource not found",
            "status_code": 404
        }
    )


# --------------------------------------------------
# Validation Error Handler
# --------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):

    logger.warning(
        "%s %s -> 422",
        request.method,
        request.url.path
    )

    error = exc.errors()[0]

    message = error.get(
        "msg",
        "Invalid request"
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": message,
            "status_code": 422
        }
    )


# --------------------------------------------------
# HTTP Exception Handler
# --------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):

    logger.warning(
        "%s %s -> %s",
        request.method,
        request.url.path,
        exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc.detail),
            "status_code": exc.status_code
        }
    )


# --------------------------------------------------
# General Exception Handler
# --------------------------------------------------

@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception
):

    logger.exception(
        "Unexpected error: %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500
        }
    )


# ==================================================
# 1. GET CUSTOMER
# ==================================================

@app.get(
    "/customer/{customer_id}",
    response_model=CustomerResponse
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None)
):

    logger.info(
        "GET /customer/%s",
        customer_id
    )

    verify_api_key(x_api_key)

    try:

        result = (
            db.query(
                Customer.customer_id,
                FactCustomerAccount.tenure,
                Contract.contract_name.label(
                    "contract_type"
                ),
                FactCustomerAccount.internet_service,
                FactCustomerAccount.monthly_charges,
                FactCustomerAccount.churn
            )
            .join(
                FactCustomerAccount,
                Customer.customer_id
                == FactCustomerAccount.customer_id
            )
            .join(
                Contract,
                FactCustomerAccount.contract_id
                == Contract.contract_id
            )
            .filter(
                Customer.customer_id == customer_id
            )
            .first()
        )


        if result is None:

            logger.warning(
                "Customer '%s' not found",
                customer_id
            )

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Customer '{customer_id}' "
                    "not found"
                )
            )


        logger.info(
            "GET /customer/%s -> 200",
            customer_id
        )


        return CustomerResponse(
            customer_id=result.customer_id,
            tenure=result.tenure,
            contract_type=result.contract_type,
            internet_service=result.internet_service,
            monthly_charges=result.monthly_charges,
            churn=result.churn
        )

    except HTTPException:
        raise

    except SQLAlchemyError as e:

        logger.error(
            "Database error for customer '%s': %s",
            customer_id,
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Database unavailable"
        )


# ==================================================
# 2. GET CHURN SUMMARY
# ==================================================

@app.get("/churn/summary")
def churn_summary(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None)
):

    logger.info(
        "GET /churn/summary"
    )
    logger.info("Received API key: %s", x_api_key)

    verify_api_key(x_api_key)

    try:

        result = get_churn_summary(db)

        logger.info(
            "GET /churn/summary -> 200"
        )
        
        return result

    except SQLAlchemyError as e:

        logger.error(
            "Database error in churn summary: %s",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Database unavailable"
        )


# ==================================================
# 3. GET HIGH-RISK CUSTOMERS
# ==================================================

@app.get(
    "/customers/high-risk",
    response_model=list[HighRiskCustomerResponse]
)
def high_risk_customers(
    limit: int = 50,
    min_tenure: int | None = None,
    max_tenure: int | None = None,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None)
):

    logger.info(
        "GET /customers/high-risk "
        "limit=%s min_tenure=%s max_tenure=%s",
        limit,
        min_tenure,
        max_tenure
    )

    verify_api_key(x_api_key)

    try:

        result = get_high_risk_customers(
            db=db,
            limit=limit,
            min_tenure=min_tenure,
            max_tenure=max_tenure
        )

        logger.info(
            "GET /customers/high-risk -> 200"
        )

        return result

    except SQLAlchemyError as e:

        logger.error(
            "Database error in high-risk customers: %s",
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Database unavailable"
        )


# ==================================================
# 4. GET CUSTOMER FEATURES
# ==================================================

@app.get(
    "/customer/{customer_id}/features",
    response_model=CustomerFeatures
)
def customer_features(
    customer_id: str,
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None)
):

    logger.info(
        "GET /customer/%s/features",
        customer_id
    )

    verify_api_key(x_api_key)

    try:

        result = get_customer_features(
            db,
            customer_id
        )

        if result is None:

            logger.warning(
                "Features for customer '%s' not found",
                customer_id
            )

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Features for customer "
                    f"'{customer_id}' not found"
                )
            )

        logger.info(
            "GET /customer/%s/features -> 200",
            customer_id
        )

        return CustomerFeatures(
            service_count=result.service_count,
            tenure_bucket=result.tenure_bucket,
            high_charge_flag=result.high_charge_flag,
            is_long_term_customer=result.is_long_term_customer,
            has_streaming_bundle=result.has_streaming_bundle,
            auto_pay_flag=result.auto_pay_flag,
            monthly_charges=result.monthly_charges,
            total_charges=result.total_charges
        )

    except HTTPException:
        raise

    except SQLAlchemyError as e:

        logger.error(
            "Database error for customer features '%s': %s",
            customer_id,
            e
        )

        raise HTTPException(
            status_code=500,
            detail="Database unavailable"
        )


# ==================================================
# 5. POST PREDICT CHURN
# ==================================================

@app.post("/predict-churn")
def predict_churn_endpoint(
    request: ChurnPredictionRequest,
    x_api_key: str | None = Header(default=None)
):

    logger.info(
        "POST /predict-churn "
        "tenure=%s monthly_charges=%s "
        "contract_type=%s service_count=%s",
        request.tenure,
        request.monthly_charges,
        request.contract_type,
        request.service_count
    )

    verify_api_key(x_api_key)

    logger.info(
        "POST /predict-churn -> 200"
    )

    result = predict_churn(
        tenure=request.tenure,
        monthly_charges=request.monthly_charges,
        contract_type=request.contract_type,
        service_count=request.service_count
    )

    return result