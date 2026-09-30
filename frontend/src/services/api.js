import axios from "axios";


const API_BASE_URL =
  "http://127.0.0.1:8000";


const api = axios.create({

  baseURL: API_BASE_URL,

  headers: {
    "Content-Type":
      "application/json",
  },

});


export async function analyzeScholarshipUrl(
  url
) {

  const response =
    await api.post(
      "/api/analyze-url",
      {
        url,
      }
    );

  return response.data;
}


export async function checkEligibility(
  criteria,
  userData
) {

  const response =
    await api.post(
      "/api/check-eligibility",
      {

        criteria,

        user_data:
          userData,

      }
    );

  return response.data;
}


export default api;