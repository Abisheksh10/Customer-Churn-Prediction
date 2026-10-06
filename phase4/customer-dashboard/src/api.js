import axios from "axios";

export const BASE_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const API_KEY = import.meta.env.VITE_API_KEY;

console.log("API URL:", BASE_URL);
console.log("API KEY exists:", !!API_KEY);

const api = axios.create({
    baseURL: BASE_URL,
    headers: {
        "X-API-Key": API_KEY
    }
});

export default api;