import { useState } from "react";
import api from "../api";
import "./ChurnPrediction.css";

function ChurnPrediction() {

    const [formData, setFormData] = useState({
        tenure: "",
        monthly_charges: "",
        contract_type: "Month-to-month",
        service_count: ""
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    const handleChange = (e) => {

        const { name, value } = e.target;

        setFormData({
            ...formData,
            [name]: value
        });

    };


    const handleSubmit = async (e) => {

        e.preventDefault();

        setLoading(true);
        setError("");
        setResult(null);

        try {

            const response = await api.post(
                "/predict-churn",
                {
                    tenure: Number(formData.tenure),
                    monthly_charges: Number(
                        formData.monthly_charges
                    ),
                    contract_type: formData.contract_type,
                    service_count: Number(
                        formData.service_count
                    )
                }
            );

            console.log(
                "Churn Prediction:",
                response.data
            );

            setResult(response.data);

        } catch (error) {

            console.error(
                "Prediction API Error:",
                error
            );

            /*
             * FastAPI/Pydantic validation error
             */
            if (error.response?.status === 422) {

                const validationDetail =
                    error.response.data?.detail;

                if (Array.isArray(validationDetail)) {

                    const messages =
                        validationDetail.map(
                            (item) =>
                                item.msg
                        );

                    setError(
                        messages.join(". ")
                    );

                } else {

                    setError(
                        String(validationDetail)
                    );

                }

            } else {

                setError(
                    error.response?.data?.detail ||
                    "Failed to get churn prediction."
                );

            }

        } finally {

            setLoading(false);

        }

    };


    /*
     * Determine risk level from risk_score
     */
    const getRiskLevel = (riskScore) => {

        if (riskScore < 0.3) {
            return "low";
        }

        if (riskScore <= 0.6) {
            return "medium";
        }

        return "high";

    };


    const riskLevel = result
        ? getRiskLevel(result.risk_score)
        : "";


    return (

        <div className="prediction-page">

            {/* Header */}

            <div className="prediction-header">

                <h1>
                    Churn Prediction
                </h1>

                <p>
                    Enter customer details to estimate
                    their likelihood of churning.
                </p>

            </div>


            <div className="prediction-layout">

                {/* Form */}

                <div className="prediction-card">

                    <h2>
                        Customer Information
                    </h2>

                    <p className="form-description">
                        Provide the customer's current
                        information for a churn prediction.
                    </p>


                    <form
                        onSubmit={handleSubmit}
                        className="prediction-form"
                    >

                        {/* Tenure */}

                        <div className="form-group">

                            <label htmlFor="tenure">
                                Tenure
                                <span> (months)</span>
                            </label>

                            <input
                                id="tenure"
                                type="number"
                                name="tenure"
                                value={formData.tenure}
                                onChange={handleChange}
                                min="0"
                                max="100"
                                placeholder="e.g. 12"
                                required
                            />

                        </div>


                        {/* Monthly Charges */}

                        <div className="form-group">

                            <label htmlFor="monthly_charges">
                                Monthly Charges
                            </label>

                            <input
                                id="monthly_charges"
                                type="number"
                                name="monthly_charges"
                                value={
                                    formData.monthly_charges
                                }
                                onChange={handleChange}
                                min="0.01"
                                step="0.01"
                                placeholder="e.g. 79.95"
                                required
                            />

                        </div>


                        {/* Contract Type */}

                        <div className="form-group">

                            <label htmlFor="contract_type">
                                Contract Type
                            </label>

                            <select
                                id="contract_type"
                                name="contract_type"
                                value={
                                    formData.contract_type
                                }
                                onChange={handleChange}
                            >

                                <option value="Month-to-month">
                                    Month-to-month
                                </option>

                                <option value="One year">
                                    One year
                                </option>

                                <option value="Two year">
                                    Two year
                                </option>

                            </select>

                        </div>


                        {/* Service Count */}

                        <div className="form-group">

                            <label htmlFor="service_count">
                                Service Count
                                <span> (0–6)</span>
                            </label>

                            <input
                                id="service_count"
                                type="number"
                                name="service_count"
                                value={
                                    formData.service_count
                                }
                                onChange={handleChange}
                                min="0"
                                max="6"
                                placeholder="e.g. 3"
                                required
                            />

                        </div>


                        {/* Error */}

                        {error && (

                            <div className="prediction-error">
                                <strong>
                                    Validation Error
                                </strong>

                                <p>
                                    {error}
                                </p>
                            </div>

                        )}


                        {/* Submit */}

                        <button
                            type="submit"
                            className="predict-button"
                            disabled={loading}
                        >

                            {loading ? (
                                <>
                                    <span className="button-spinner"></span>
                                    Predicting...
                                </>
                            ) : (
                                "Predict Churn"
                            )}

                        </button>

                    </form>

                </div>


                {/* Result */}

                <div className="prediction-result-card">

                    {!result ? (

                        <div className="result-empty">

                            <div className="result-empty-icon">
                                ?
                            </div>

                            <h2>
                                Prediction Result
                            </h2>

                            <p>
                                Submit the customer information
                                to see the churn prediction.
                            </p>

                        </div>

                    ) : (

                        <div className="prediction-result">

                            <div className="result-title">
                                Prediction Result
                            </div>


                            {/* Risk Indicator */}

                            <div
                                className={`risk-indicator ${riskLevel}`}
                            >

                                <div className="risk-score">

                                    {
                                        (
                                            result.risk_score * 100
                                        ).toFixed(1)
                                    }%

                                </div>

                                <div className="risk-label">
                                    Churn Risk
                                </div>

                            </div>


                            {/* Prediction */}

                            <div className="prediction-text">

                                <span className="result-label">
                                    Prediction
                                </span>

                                <h2>
                                    {result.prediction}
                                </h2>

                            </div>


                            {/* Confidence */}

                            <div className="confidence-section">

                                <span className="result-label">
                                    Confidence Level
                                </span>

                                <span
                                    className={`confidence-badge ${riskLevel}`}
                                >
                                    {riskLevel === "low"
                                        ? "Low Risk"
                                        : riskLevel === "medium"
                                            ? "Medium Risk"
                                            : "High Risk"
                                    }
                                </span>

                            </div>


                            {/* Customer ID */}

                            {result.customer_id && (
                                <div className="customer-result">

                                    <span className="result-label">
                                        Customer ID
                                    </span>

                                    <strong>
                                        {result.customer_id}
                                    </strong>

                                </div>
                            )}


                            {/* Stub Note */}

                            {result.note && (

                                <div className="prediction-note">

                                    {result.note}

                                </div>

                            )}

                        </div>

                    )}

                </div>

            </div>

        </div>

    );
}

export default ChurnPrediction;