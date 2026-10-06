import { useEffect, useState } from "react";
import api from "../api";
import "./HighRiskCustomers.css";

function HighRiskCustomers() {

    const [customers, setCustomers] = useState([]);
    const [limit, setLimit] = useState(50);
    const [sortAsc, setSortAsc] = useState(true);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");


    // Fetch high-risk customers
    useEffect(() => {

        const fetchHighRiskCustomers = async () => {

            try {

                setLoading(true);
                setError("");

                const response = await api.get(
                    "/customers/high-risk",
                    {
                        params: {
                            limit: limit
                        }
                    }
                );

                console.log(
                    "High-risk customers:",
                    response.data
                );

                setCustomers(response.data);

            } catch (error) {

                console.error(
                    "High-risk API Error:",
                    error
                );

                setError(
                    "Failed to load high-risk customers."
                );

            } finally {

                setLoading(false);

            }
        };

        fetchHighRiskCustomers();

    }, [limit]);


    // Sort customers by tenure
    const sortedCustomers = [...customers].sort(
        (a, b) => {

            if (sortAsc) {
                return a.tenure - b.tenure;
            }

            return b.tenure - a.tenure;

        }
    );


    // Toggle tenure sorting
    const toggleTenureSort = () => {

        setSortAsc(!sortAsc);

    };


    // Load 50 more customers
    const loadMore = () => {

        setLimit(limit + 50);

    };


    if (loading) {

        return (
            <div className="high-risk-loading">

                <div className="high-risk-spinner"></div>

                <p>
                    Loading high-risk customers...
                </p>

            </div>
        );

    }


    if (error) {

        return (
            <div className="high-risk-error">
                {error}
            </div>
        );

    }


    return (

        <div className="high-risk-page">

            {/* Header */}

            <div className="high-risk-header">

                <div>
                    <h1>High-Risk Customers</h1>

                    <p>
                        Customers identified as high risk based on
                        the current retention rules.
                    </p>
                </div>

            </div>


            {/* Count Banner */}

            <div className="risk-count-banner">

                <div className="count-number">
                    {customers.length}
                </div>

                <div className="count-text">
                    high-risk customers identified
                </div>

            </div>


            {/* Empty State */}

            {customers.length === 0 ? (

                <div className="no-customers">

                    <div className="empty-icon">
                        ✓
                    </div>

                    <h2>
                        No high-risk customers found
                    </h2>

                    <p>
                        There are currently no customers matching
                        the high-risk criteria.
                    </p>

                </div>

            ) : (

                <>

                    {/* Table */}

                    <div className="risk-table-container">

                        <table className="risk-table">

                            <thead>

                                <tr>

                                    <th>
                                        Customer ID
                                    </th>

                                    <th
                                        className="sortable-header"
                                        onClick={toggleTenureSort}
                                    >
                                        <span>
                                            Tenure
                                        </span>

                                        <span className="sort-icon">
                                            {sortAsc ? "▲" : "▼"}
                                        </span>
                                    </th>

                                    <th>
                                        Monthly Charges
                                    </th>

                                    <th>
                                        Contract Type
                                    </th>

                                    <th>
                                        Risk Reason
                                    </th>

                                </tr>

                            </thead>


                            <tbody>

                                {sortedCustomers.map(
                                    (customer) => (

                                        <tr
                                            key={
                                                customer.customer_id
                                            }
                                        >

                                            <td className="customer-id">
                                                {customer.customer_id}
                                            </td>


                                            <td>
                                                {customer.tenure} months
                                            </td>


                                            <td className="charges">
                                                $
                                                {Number(
                                                    customer.monthly_charges
                                                ).toFixed(2)}
                                            </td>


                                            <td>

                                                <span className="contract-badge">
                                                    {
                                                        customer.contract_type
                                                    }
                                                </span>

                                            </td>


                                            <td className="risk-reason">
                                                {
                                                    customer.risk_reason
                                                }
                                            </td>

                                        </tr>

                                    )
                                )}

                            </tbody>

                        </table>

                    </div>


                    {/* Load More */}

                    <div className="load-more-container">

                        <button
                            className="load-more-button"
                            onClick={loadMore}
                        >
                            Load More
                        </button>

                    </div>

                </>

            )}

        </div>

    );
}

export default HighRiskCustomers;