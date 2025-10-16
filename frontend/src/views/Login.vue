<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>Quiz App</h1>
        <p>{{ isRegister ? 'Create your account' : 'Sign in to your account' }}</p>
      </div>
      
      <form @submit.prevent="handleSubmit" class="login-form">
        <div v-if="isRegister" class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            placeholder="Enter your email"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="Enter your username"
            required
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="Enter your password"
            required
          />
        </div>
        
        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In') }}
        </button>
        
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <div v-if="success" class="success-message">
          {{ success }}
        </div>
      </form>
      
      <div class="login-footer">
        <p>
          {{ isRegister ? 'Already have an account?' : "Don't have an account?" }}
          <a href="#" @click="toggleMode">
            {{ isRegister ? 'Sign In' : 'Create Account' }}
          </a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'Login',
  data() {
    return {
      isRegister: false,
      loading: false,
      error: '',
      success: '',
      formData: {
        username: '',
        email: '',
        password: ''
      }
    }
  },
  methods: {
    toggleMode() {
      this.isRegister = !this.isRegister
      this.error = ''
      this.success = ''
      this.formData = {
        username: '',
        email: '',
        password: ''
      }
    },
    
    async handleSubmit() {
      this.loading = true
      this.error = ''
      this.success = ''
      
      try {
        if (this.isRegister) {
          await api.register(this.formData)
          this.success = 'Account created successfully! Please sign in.'
          this.isRegister = false
          this.formData = {
            username: '',
            email: '',
            password: ''
          }
        } else {
          const response = await api.login({
            username: this.formData.username,
            password: this.formData.password
          })
          
          const { access_token, user } = response.data
          localStorage.setItem('token', access_token)
          localStorage.setItem('user', JSON.stringify(user))
          localStorage.setItem('userRole', user.role)
          
          if (user.role === 'admin') {
            this.$router.push('/admin')
          } else {
            this.$router.push('/dashboard')
          }
        }
      } catch (error) {
        this.error = error.response?.data?.message || 'An error occurred'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  color: #1f2937;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.login-header p {
  color: #6b7280;
  font-size: 0.875rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  color: #374151;
  font-weight: 500;
  font-size: 0.875rem;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.error-message {
  color: #dc2626;
  font-size: 0.875rem;
  text-align: center;
  padding: 0.75rem;
  background: #fef2f2;
  border-radius: 8px;
}

.success-message {
  color: #059669;
  font-size: 0.875rem;
  text-align: center;
  padding: 0.75rem;
  background: #ecfdf5;
  border-radius: 8px;
}

.login-footer {
  text-align: center;
  margin-top: 2rem;
}

.login-footer p {
  color: #6b7280;
  font-size: 0.875rem;
}

.login-footer a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>