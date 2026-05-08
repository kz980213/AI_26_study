<template>
    <div>
        <h1>this is 首页</h1>
        <button @click="fetchUsers">查看用户列表</button>
        <button @click="goToStream">流式输出演示页</button>
        <button @click="logout">退出登录</button>
    </div>
</template>
<script lang="ts" setup>
import router from "@/router";
import { removeToken } from "../utils/storage";

const logout = () => {
    removeToken();
    alert('已退出登录！');
    router.push('/login')
};

const fetchUsers = () => {
    router.push('/allUsers')
}

const goToStream = () => {
    router.push('/stream')
}
</script>