# API Contract v1

## Base URL
http://127.0.0.1:8000

## Auth 方式
Bearer Token

## 通用说明
- 登录成功后返回 access_token
- 需要鉴权的接口，在请求头中传：
  Authorization: Bearer <token>


  ## 1. 用户注册
- 方法：POST
- 路径：/auth/register
- 请求体：
```json
{
  "username": "kk",
  "password": "123456"
}
```响应
{
  "message": "Register success"
}
    ## 2. 用户登录
- 方法：POST
- 路径：/auth/login
- 请求体：
```json
{
  "username": "kk",
  "password": "123456"
}
```响应
{
  "access_token": "xxxxx",
  "token_type": "bearer"
}
    ## 3. 获取当前用户
- 方法：GET
- 路径：/users/me
- 请求头：
Authorization: Bearer <token>
```响应
{
  "username": "kk"
}
    ## 4. 修改密码
- 方法：PUT
- 路径：/users/me/password
-请求头：
Authorization: Bearer <token>
- 请求体：
```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```响应
{
  "message": "Password updated successfully"
}


---

### 第三步：补错误响应格式


```md
## 错误响应格式

### 业务错误
```json
{
  "code": 400,
  "message": "Username already exists"
}
参数校验错误：
{
  "code": 422,
  "message": "Request validation failed",
  "errors": [...]
}

---

### 第四步：写联调顺序



## 推荐联调顺序
1. 先调 POST /auth/register
2. 再调 POST /auth/login 获取 token
3. 用 token 调 GET /users/me
4. 再调 PUT /users/me/password

## 当前接口范围
- POST /auth/register
- POST /auth/login
- GET /users/me
- PUT /users/me/password

## 当前返回格式
### 成功
各接口按各自 schema 返回

### 业务错误
{
  "code": 400,
  "message": "..."
}

### 参数校验错误
{
  "code": 422,
  "message": "Request validation failed",
  "errors": [...]
}

## 下周前端联调建议顺序
1. 先接登录页
2. 完成 token 存储
3. 接 /users/me 获取登录态
4. 接修改密码页