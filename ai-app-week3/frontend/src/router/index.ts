import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import UsersView from '../views/UsersView.vue'
import StreamView from '../views/StreamDemoView.vue'
import ChatView from '../views/ChatView.vue'
import TaskParserView from '../views/TaskParserView.vue'
import KnowledgeView from '../views/KnowledgeIngestView.vue'
import AiChatView from '../views/AiChatView.vue'
import ChatStreamView from '../views/ChatStreamView.vue'
import StructuredTaskView from '../views/StructuredTaskView.vue'
import ToolCallingView from '../views/ToolCallingView.vue'
import DocumentIngestionView from '../views/DocumentIngestionView.vue'
import { getToken } from '../utils/storage'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login',
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/home',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/allUsers',
      name: 'allUsers',
      component: UsersView,
    },
    {
      path: '/stream',
      name: 'stream',
      component: StreamView,
    },
    {
      path: '/chat',
      name: 'chat',
      component: ChatView,
    },
    {
      path: '/task-parser',
      name: 'taskParser',
      component: TaskParserView,
    },
    {
      path: '/knowledge',
      name: 'knowledge',
      component: KnowledgeView,
    },
    {
      path: '/ai-chat',
      name: 'aiChat',
      component: AiChatView,
    },
    {
      path: '/chatStreamView',
      name: 'chatStreamView',
      component: ChatStreamView,
    },
    {
      path: '/structured-tasks',
      name: 'structuredTasks',
      component: StructuredTaskView,
    },
    {
      path: '/tool-calling',
      name: 'toolCalling',
      component: ToolCallingView,
    },
    {
      path: '/document-ingestion',
      name: 'documentIngestion',
      component: DocumentIngestionView,
    }
  ],
  
})

router.beforeEach((to, from, next) => {
    const token = getToken()
    if (!token && to.path !== '/login') {
        next('/login')
        return;
    } 
    if (token && to.path === '/login') {
        next('/home')
        return;
    }
    next()
})


export default router