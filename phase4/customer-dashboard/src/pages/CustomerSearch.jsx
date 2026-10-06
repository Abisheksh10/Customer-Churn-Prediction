import { useState } from "react";
import api from "../api";

function CustomerSearch() {

    const [customerId, setCustomerId] = useState("");
    const [customer, setCustomer] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const searchCustomer = async () => {

        if (!customerId.trim()) {
            setError("Please enter a customer ID");
            setCustomer(null);
            return;
        }

        setLoading(true);
        setError("");
        setCustomer(null);

        try {

            const response = await api.get(
                `/customer/${customerId.trim()}`
            );

            setCustomer(response.data);

        } catch (e) {

            if (e.response?.status === 404) {

                setError("Customer not found");

            } else {

                setError("Failed to fetch customer details");

            }

        } finally {

            setLoading(false);

        }
    };


    return (
        <div>

            <h2>Customer Search</h2>

            <div>

                <input
                    type="text"
                    placeholder="Enter Customer ID"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                />

                <button onClick={searchCustomer}>
                    Search
                </button>

            </div>


            {loading && (
                <p>Loading...</p>
            )}


            {error && (
                <p>{error}</p>
            )}


            {customer && (
                <div>

                    <h3>Customer Profile</h3>

                    <p>
                        <strong>Customer ID:</strong>{" "}
                        {customer.customer_id}
                    </p>

                    <p>
                        <strong>Tenure:</strong>{" "}
                        {customer.tenure} months
                    </p>

                    <p>
                        <strong>Contract:</strong>{" "}
                        {customer.contract_type}
                    </p>

                    <p>
                        <strong>Internet Service:</strong>{" "}
                        {customer.internet_service}
                    </p>

                    <p>
                        <strong>Monthly Charges:</strong>{" "}
                        ₹{customer.monthly_charges}
                    </p>

                    <p>
                        <strong>Churn Status:</strong>{" "}

                        <span
                            style={{
                                backgroundColor:
                                    customer.churn === 1
                                        ? "red"
                                        : "green",
                                color: "white",
                                padding: "5px 10px",
                                borderRadius: "5px"
                            }}
                        >
                            {customer.churn === 1
                                ? "Churned"
                                : "Active"}
                        </span>

                    </p>

                </div>
            )}

        </div>
    );
}

export default CustomerSearch;