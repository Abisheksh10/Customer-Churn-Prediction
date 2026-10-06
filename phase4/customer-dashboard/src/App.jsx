import { useEffect, useState } from "react";
import api from "./api";
import CustomerSearch from "./pages/CustomerSearch"
import ChurnSummary from "./pages/ChurnSummary";
import HighRiskCustomers from "./pages/HighRiskCustomers";
import ChurnPrediction from "./pages/ChurnPrediction";

function App() {

    const [page,setPage]=useState("")


    return (
        <div>
            <h1>Customer Retention Dashboard</h1>

            <nav>
               
            </nav>
            

            <nav className="navbar">

                <h2>Customer Retention Dashboard</h2>

                <div className="nav-links">
                    <button onClick={()=>setPage("search")}>Customer Search</button>
                    <button className={
                            page === "summary"
                                ? "active"
                                : ""
                        }
                        onClick={() => setPage("summary")}
                    >
                        Churn Analytics
                    </button>
                    
                    <button className={
                            page === "high-risk"
                                ? "active"
                                : ""
                        } onClick={()=>setPage("high-risk")}>High Risk Customers</button>

                    <button
                    className={
                        page === "prediction"
                                ? "active"
                                : ""
                        }
                        onClick={() => setPage("prediction")}>
                        Churn Prediction
                    </button>
                </div>

            </nav>
            {page === "search" && (
                <CustomerSearch />
            )}

            {page === "summary" && <ChurnSummary />}
             {page === "high-risk" && (
                <HighRiskCustomers />
            )}
            {page === "prediction" && (
    <ChurnPrediction />
)}
        </div>
    );
}

export default App;