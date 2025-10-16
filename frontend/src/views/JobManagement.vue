<template>
  <div class="job-management-container">
    <!-- Header -->
    <header class="job-header">
      <div class="header-content">
        <div class="header-left">
          <h1>Job Management</h1>
          <p>Test and monitor automated jobs</p>
        </div>
        <div class="header-right">
          <button @click="$router.push('/admin')" class="btn-outline">
            Back to Admin Dashboard
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="job-main">
      <!-- Job Testing Section -->
      <div class="content-section">
        <div class="section-header">
          <h2>Test Jobs</h2>
          <p>Manually trigger automated jobs for testing</p>
        </div>
        
        <div class="job-cards">
          <!-- Test User Reminders -->
          <div class="job-card">
            <div class="job-icon">📧</div>
            <div class="job-info">
              <h3>User Reminders</h3>
              <p>Send reminder emails to inactive users (users who haven't taken a quiz in the last 7 days)</p>
              )
            </div>
            <div class="job-actions">
              <button 
                @click="testUserReminders" 
                :disabled="loading.reminders"
                class="btn-primary"
              >
                {{ loading.reminders ? 'Sending...' : 'Test Reminders' }}
              </button>
            </div>
          </div>

          

          <!-- Test Cleanup -->
          <div class="job-card">
            <div class="job-icon">🧹</div>
            <div class="job-info">
              <h3>Weekly Cleanup</h3>
              <p>Clean up old logs and temporary data</p>
            </div>
            <div class="job-actions">
              <button 
                @click="testCleanup" 
                :disabled="loading.cleanup"
                class="btn-primary"
              >
                {{ loading.cleanup ? 'Running...' : 'Test Cleanup' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Job Information Section -->
      <div class="content-section">
        <div class="section-header">
          <h2>Job Information</h2>
          <div class="info-actions">
            <button @click="getInactiveUsers" :disabled="loading.inactiveUsers" class="btn-outline">
              {{ loading.inactiveUsers ? 'Loading...' : 'View Inactive Users' }}
            </button>
            <button @click="getDailyStats" :disabled="loading.dailyStats" class="btn-outline">
              {{ loading.dailyStats ? 'Loading...' : 'View Daily Stats' }}
            </button>
          </div>
        </div>

        <!-- Inactive Users -->
        <div v-if="inactiveUsers.length > 0" class="info-card">
          <h3>Inactive Users ({{ inactiveUsers.length }})</h3>
          <div class="users-list">
            <div v-for="user in inactiveUsers" :key="user.id" class="user-item">
              <div class="user-info">
                <span class="username">{{ user.username }}</span>
                <span class="email">{{ user.email }}</span>
              </div>
              <div class="user-stats">
                <span class="attempts">{{ user.total_attempts }} attempts</span>
                <span class="last-attempt">
                  Last: {{ user.last_attempt ? formatDate(user.last_attempt) : 'Never' }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Daily Stats -->
        <div v-if="dailyStats" class="info-card">
          <h3>Daily Statistics</h3>
          <div class="stats-grid">
            <div class="stat-section">
              <h4>Today</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <span class="stat-label">Active Users:</span>
                  <span class="stat-value">{{ dailyStats.today.active_users }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Total Attempts:</span>
                  <span class="stat-value">{{ dailyStats.today.total_attempts }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Average Score:</span>
                  <span class="stat-value">{{ dailyStats.today.avg_score }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Quizzes Taken:</span>
                  <span class="stat-value">{{ dailyStats.today.quizzes_taken }}</span>
                </div>
              </div>
            </div>

            <div class="stat-section">
              <h4>Yesterday</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <span class="stat-label">Active Users:</span>
                  <span class="stat-value">{{ dailyStats.yesterday.active_users }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Total Attempts:</span>
                  <span class="stat-value">{{ dailyStats.yesterday.total_attempts }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Average Score:</span>
                  <span class="stat-value">{{ dailyStats.yesterday.avg_score }}%</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Quizzes Taken:</span>
                  <span class="stat-value">{{ dailyStats.yesterday.quizzes_taken }}</span>
                </div>
              </div>
            </div>

            <div class="stat-section full-width">
              <h4>Additional Info</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <span class="stat-label">New Users Today:</span>
                  <span class="stat-value">{{ dailyStats.new_users }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Top Quiz:</span>
                  <span class="stat-value">{{ dailyStats.top_quiz.title }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Top Quiz Attempts:</span>
                  <span class="stat-value">{{ dailyStats.top_quiz.attempts }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Top Quiz Avg Score:</span>
                  <span class="stat-value">{{ dailyStats.top_quiz.avg_score }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Job Results Section -->
      <div v-if="jobResults.length > 0" class="content-section">
        <div class="section-header">
          <h2>Job Results</h2>
          <button @click="clearResults" class="btn-outline">Clear Results</button>
        </div>
        
        <div class="results-list">
          <div 
            v-for="(result, index) in jobResults" 
            :key="index" 
            class="result-item"
            :class="result.success ? 'success' : 'error'"
          >
            <div class="result-header">
              <span class="result-type">{{ result.type }}</span>
              <span class="result-time">{{ formatDateTime(result.timestamp) }}</span>
            </div>
            <div class="result-message">{{ result.message }}</div>
            <div v-if="result.details" class="result-details">{{ result.details }}</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'JobManagement',
  data() {
    return {
      loading: {
        reminders: false,
        adminReport: false,
        cleanup: false,
        inactiveUsers: false,
        dailyStats: false
      },
      inactiveUsers: [],
      dailyStats: null,
      jobResults: []
    }
  },
  methods: {
    async testUserReminders() {
      this.loading.reminders = true
      try {
        const response = await api.testUserReminders()
        this.addJobResult({
          type: 'User Reminders',
          success: true,
          message: response.data.message,
          details: `Sent ${response.data.count} reminder emails`
        })
      } catch (error) {
        this.addJobResult({
          type: 'User Reminders',
          success: false,
          message: 'Failed to send reminders',
          details: error.response?.data?.message || error.message
        })
      } finally {
        this.loading.reminders = false
      }
    },

    async testAdminReport() {
      this.loading.adminReport = true
      try {
        const response = await api.testAdminReport()
        this.addJobResult({
          type: 'Admin Report',
          success: true,
          message: response.data.message,
          details: `Sent ${response.data.count} admin report emails`
        })
      } catch (error) {
        this.addJobResult({
          type: 'Admin Report',
          success: false,
          message: 'Failed to send admin report',
          details: error.response?.data?.message || error.message
        })
      } finally {
        this.loading.adminReport = false
      }
    },

    async testCleanup() {
      this.loading.cleanup = true
      try {
        const response = await api.testCleanup()
        this.addJobResult({
          type: 'Weekly Cleanup',
          success: response.data.success,
          message: response.data.message,
          details: response.data.success ? 'Cleanup completed successfully' : 'Cleanup failed'
        })
      } catch (error) {
        this.addJobResult({
          type: 'Weekly Cleanup',
          success: false,
          message: 'Failed to run cleanup',
          details: error.response?.data?.message || error.message
        })
      } finally {
        this.loading.cleanup = false
      }
    },

    async getInactiveUsers() {
      this.loading.inactiveUsers = true
      try {
        const response = await api.getInactiveUsers()
        this.inactiveUsers = response.data.users
        this.addJobResult({
          type: 'Inactive Users',
          success: true,
          message: response.data.message,
          details: `Found ${response.data.users.length} inactive users`
        })
      } catch (error) {
        this.addJobResult({
          type: 'Inactive Users',
          success: false,
          message: 'Failed to get inactive users',
          details: error.response?.data?.message || error.message
        })
      } finally {
        this.loading.inactiveUsers = false
      }
    },

    async getDailyStats() {
      this.loading.dailyStats = true
      try {
        const response = await api.getDailyStats()
        this.dailyStats = response.data.stats
        this.addJobResult({
          type: 'Daily Stats',
          success: true,
          message: response.data.message,
          details: 'Daily statistics retrieved successfully'
        })
      } catch (error) {
        this.addJobResult({
          type: 'Daily Stats',
          success: false,
          message: 'Failed to get daily stats',
          details: error.response?.data?.message || error.message
        })
      } finally {
        this.loading.dailyStats = false
      }
    },

    addJobResult(result) {
      this.jobResults.unshift({
        ...result,
        timestamp: new Date()
      })
      // Keep only last 10 results
      if (this.jobResults.length > 10) {
        this.jobResults = this.jobResults.slice(0, 10)
      }
    },

    clearResults() {
      this.jobResults = []
    },

    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },

    formatDateTime(date) {
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.job-management-container {
  min-height: 100vh;
  background: #f8fafc;
}

.job-header {
  background: white;
  border-bottom: 1px solid #e5e7eb;
  padding: 1rem 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left h1 {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.header-left p {
  color: #6b7280;
  font-size: 0.875rem;
}

.btn-outline {
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  color: #3b82f6;
  background: transparent;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  background: #3b82f6;
  color: white;
}

.job-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.content-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.section-header h2 {
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.section-header p {
  color: #6b7280;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.info-actions {
  display: flex;
  gap: 1rem;
}

.job-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
}

.job-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.job-icon {
  font-size: 2rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #dbeafe;
  border-radius: 50%;
}

.job-info {
  flex: 1;
}

.job-info h3 {
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.job-info p {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.4;
}

.job-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.info-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.info-card h3 {
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.username {
  font-weight: 500;
  color: #1f2937;
}

.email {
  font-size: 0.875rem;
  color: #6b7280;
}

.user-stats {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  text-align: right;
}

.attempts,
.last-attempt {
  font-size: 0.875rem;
  color: #6b7280;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.stat-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
}

.stat-section.full-width {
  grid-column: 1 / -1;
}

.stat-section h4 {
  color: #1f2937;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.stat-items {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
}

.stat-value {
  color: #1f2937;
  font-weight: 500;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.result-item.success {
  background: #f0fdf4;
  border-left-color: #10b981;
}

.result-item.error {
  background: #fef2f2;
  border-left-color: #ef4444;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.result-type {
  font-weight: 600;
  color: #1f2937;
}

.result-time {
  font-size: 0.875rem;
  color: #6b7280;
}

.result-message {
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.result-details {
  font-size: 0.875rem;
  color: #6b7280;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .section-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .info-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .job-cards {
    grid-template-columns: 1fr;
  }
  
  .job-card {
    flex-direction: column;
    text-align: center;
  }
  
  .user-item {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .user-stats {
    text-align: left;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-section.full-width {
    grid-column: 1;
  }
}
</style>