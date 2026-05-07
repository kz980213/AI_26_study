<template>
    <div>
        <h1>所有用户列表</h1>
        <div v-if="isLoading">
            <p>加载中...</p>
        </div>
        <div v-else-if="errorMessage">
            <p>{{ errorMessage }}</p>
        </div>
        <div v-else-if="userList.length === 0">
            <p>没有用户数据！</p>
        </div>
        <div v-else>
            <ul>
                <li v-for="user in userList" :key="user.username">
                    {{ user.username }}
                </li>
            </ul>
        </div>
        <button @click="fetchUsers">刷新用户列表</button>
        <button @click="goToHome">返回首页</button>
    </div>
</template>
<script lang="ts" setup>
import { ref, onMounted } from "vue";
import { getUsersApi } from "../api/users";
import router from "@/router";

const isLoading = ref(false);
const errorMessage = ref('')
const userList = ref([])

const fetchUsers  = async () => {
    isLoading.value = true;
    try {
        const response = await getUsersApi();
        console.log('用户列表:', response.data);
        userList.value = response.data;
    } catch (error) {
        console.error('Failed to fetch users:', error);
        errorMessage.value = '获取用户列表失败！';
    } finally {
        isLoading.value = false;
    }
}

const goToHome = () => {
    router.push('/home')
}

onMounted(() => {
    fetchUsers()
})

</script>