import http from "./http";
export function loginApi(data:{username:string,password:string}){ 
    return http.post('/auth/login', data)
}

export function getMeApi() {
    return http.get('/users/me')
}