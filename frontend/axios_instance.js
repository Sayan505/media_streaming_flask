import axios from "axios";


const axios_client = axios.create({
    baseURL: `${process.env.BACKEND_URL}`
});

axios_client.interceptors.request.use(function (config) {
    const jwt = localStorage.getItem("jwt");

    if(jwt) {
        config.headers.Authorization = "Bearer " + jwt;
    }

    return config;
});


export default axios_client;

