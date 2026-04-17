<template>
    <div>
        <div>用户名： <input type="text" v-model="userInfo.username" /></div>
        <div>密码： <input type="password" v-model="userInfo.password" /></div>
        <button @click="login">登录</button>
        <button @click="logout">退出登录</button>
        <button @click="getMe">获取用户信息</button>
    </div>
</template>
<script lang="ts" setup>
import { loginApi, getMeApi } from "../api/auth";
import { reactive, ref } from "vue";
import { setToken, removeToken, getToken } from "../utils/storage";
const userInfo = reactive({
    username: '',
    password: ''
})
const login = async () => {
    try {
        const response = await loginApi({ 
            username: userInfo.username, 
            password: userInfo.password 
        });
        // localStorage.setItem('token', response.data.token);
        console.log('Login successful:', response.data);
        setToken(response.data.access_token);
        const me = await getMeApi()
        console.log('当前用户信息', me.data)
    } catch (error) {
        console.error('Login failed:', error);
        alert('登录失败！');
    }
};
 const logout = () => {
        removeToken()
        alert('已退出登录！');
    }
const getMe = async () => {
    let token = getToken()
    const me = await getMeApi()
    console.log('当前用户信息', me.data)
}
</script>
