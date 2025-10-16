import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import Quiz from '../views/Quiz.vue'
import QuizResult from '../views/QuizResult.vue'
import UserProfile from '../views/UserProfile.vue'
import JobManagement from '../views/JobManagement.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/quiz/:id',
    name: 'Quiz',
    component: Quiz,
    meta: { requiresAuth: true }
  },
  {
    path: '/quiz/:id/result',
    name: 'QuizResult',
    component: QuizResult,
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/jobs',
    name: 'JobManagement',
    component: JobManagement,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')
  
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!token) {
      next('/login')
    } else if (to.matched.some(record => record.meta.requiresAdmin)) {
      if (userRole !== 'admin') {
        next('/dashboard')
      } else {
        next()
      }
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router