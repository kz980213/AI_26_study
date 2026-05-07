<template>
    <div>
        <h1>this is 首页</h1>
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
</script>