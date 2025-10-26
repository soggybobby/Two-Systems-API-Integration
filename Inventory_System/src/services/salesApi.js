// services/salesApi.js
import axios from "axios";

// Base URL for Django API
const SALES_API_BASE = "http://127.0.0.1:5000/api";

export const getProductsFromSales = async () => {
  try {
    const response = await axios.get(`${SALES_API_BASE}/products/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching products from Sales_System:", error.message);
    return [];
  }
};

export const syncSaleToInventory = async (saleData) => {
  try {
    const response = await axios.post(`${SALES_API_BASE}/sales/`, saleData);
    return response.data;
  } catch (error) {
    console.error("Error sending sale data to Sales_System:", error.message);
    return null;
  }
};
