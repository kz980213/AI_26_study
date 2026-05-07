import http from "./http";
export function getUsersApi(){ 
    return http.get('/users/me/all')
}