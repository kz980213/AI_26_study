<template>
    <div>
        <h1>this is 首页</h1>
        <button @click="fetchUsers">查看用户列表</button>
        <button @click="goToStream">流式输出演示页</button>
        <button @click="goToChat">聊天页面</button>
        <button @click="goToTaskParser">进入 AI 任务解析页</button>
        <button @click="goToKnowledge">进入知识库管理页</button>
        <button @click="goToAiChat">进入 AI 聊天页</button>
        <button @click="goStructuredTasks">进入结构化任务页</button>
        <button @click="goToToolCalling">进入工具调用页</button>
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

const goToChat = () => {
    router.push('/chat')
}

const goToTaskParser = () => {
    router.push('/task-parser')
}

const goToKnowledge = () => {
    router.push('/knowledge')
}

const goToAiChat = () => {
    router.push('/ai-chat')
}

const goChatStreamView = () => {
    router.push('/chatStreamView')
}

const goStructuredTasks = () => {
    router.push('/structured-tasks')
}

const goToToolCalling = () => {
    router.push('/tool-calling')
}
</script>