import { useEffect, useState } from "react";
import api from "../api";
import "./ChurnSummary.css";

function ChurnSummary() {

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {

        const fetchChurnSummary = async () => {

            try {

                const response = await api.get("/churn/summary");

                console.log("Churn Summary:", response.data);

                setData(response.data);

            } catch (error) {

                console.error("API Error:", error);

                setError(
                    "Failed to load churn analytics. Please try again."
                );

            } finally {

                setLoading(false);

            }
        };

        fetchChurnSummary();

    }, []);


    if (loading) {
        return (
            <div className="churn-loading">
                <div className="spinner"></div>
                <p>Loading churn analytics...</p>
            </div>
        );
    }


    if (error) {
        return (
            <div className="churn-error">
                {error}
            </div>
        );
    }


    const {
        total_customers,
        churned,
        churn_rate,
        by_contract
    } = data;


    return (
        <div className="churn-page">

            <div className="churn-header">
                <h1>Churn Analytics</h1>

                <p>
                    Monitor overall customer churn and compare churn risk
                    across different contract types.
                </p>
            </div>


            {/* Metric Cards */}

            <div className="metric-grid">

                <div className="metric-card">
                    <div className="metric-icon customers-icon">
                        👥
                    </div>

                    <div>
                        <p className="metric-label">
                            Total Customers
                        </p>

                        <h2>
                            {total_customers.toLocaleString()}
                        </h2>
                    </div>
                </div>


                <div className="metric-card">
                    <div className="metric-icon churned-icon">
                        ⚠
                    </div>

                    <div>
                        <p className="metric-label">
                            Total Churned
                        </p>

                        <h2>
                            {churned.toLocaleString()}
                        </h2>
                    </div>
                </div>


                <div className="metric-card">
                    <div className="metric-icon rate-icon">
                        %
                    </div>

                    <div>
                        <p className="metric-label">
                            Churn Rate
                        </p>

                        <h2>
                            {(churn_rate * 100).toFixed(1)}%
                        </h2>
                    </div>
                </div>

            </div>


            {/* Contract Churn Section */}

            <div className="contract-section">

                <div className="section-header">
                    <div>
                        <h2>Churn Rate by Contract Type</h2>

                        <p>
                            Compare customer churn across different
                            contract types.
                        </p>
                    </div>
                </div>


                <div className="contract-table-container">

                    <table className="contract-table">

                        <thead>
                            <tr>
                                <th>Contract Type</th>
                                <th>Churn Rate</th>
                                <th>Risk Level</th>
                            </tr>
                        </thead>

                        <tbody>

                            {by_contract.map((item) => {

                                const percentage =
                                    item.churn_rate * 100;

                                let riskLevel = "Low";

                                if (percentage >= 40) {
                                    riskLevel = "High";
                                } else if (percentage >= 20) {
                                    riskLevel = "Medium";
                                }


                                return (
                                    <tr
                                        key={item.contract_type}
                                    >

                                        <td className="contract-name">
                                            {item.contract_type}
                                        </td>


                                        <td className="rate-cell">

                                            <div className="rate-wrapper">

                                                <div className="rate-bar-background">

                                                    <div
                                                        className="rate-bar"
                                                        style={{
                                                            width: `${percentage}%`
                                                        }}
                                                    ></div>

                                                </div>

                                                <span>
                                                    {percentage.toFixed(1)}%
                                                </span>

                                            </div>

                                        </td>


                                        <td>

                                            <span
                                                className={`risk-badge ${riskLevel.toLowerCase()}`}
                                            >
                                                {riskLevel}
                                            </span>

                                        </td>

                                    </tr>
                                );

                            })}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>
    );
}

export default ChurnSummary;