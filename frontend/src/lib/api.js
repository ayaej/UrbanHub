import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const http = axios.create({
  baseURL: API,
  timeout: 20000,
});

export const endpoints = {
  weather: {
    timeseries: (years = 5) => http.get(`/weather/timeseries?years=${years}`).then((r) => r.data),
    cities: () => http.get(`/weather/cities`).then((r) => r.data),
    alerts: () => http.get(`/weather/alerts`).then((r) => r.data),
  },
  mobility: {
    stations: (limit = 240) => http.get(`/mobility/stations?limit=${limit}`).then((r) => r.data),
    timeline: () => http.get(`/mobility/timeline`).then((r) => r.data),
    critical: () => http.get(`/mobility/critical`).then((r) => r.data),
  },
  pollution: {
    sensors: () => http.get(`/pollution/sensors`).then((r) => r.data),
    timeline: (city, hours = 48) =>
      http.get(`/pollution/timeline?city=${city || ""}&hours=${hours}`).then((r) => r.data),
    comparison: () => http.get(`/pollution/comparison`).then((r) => r.data),
  },
  analytics: {
    kpis: () => http.get(`/analytics/kpis`).then((r) => r.data),
    correlation: () => http.get(`/analytics/correlation`).then((r) => r.data),
    insights: () => http.get(`/analytics/insights`).then((r) => r.data),
  },
  architecture: {
    flows: () => http.get(`/architecture/flows`).then((r) => r.data),
  },
};
