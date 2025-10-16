<template>
  <div class="profile-container">
    <header class="profile-header">
      <div class="header-content">
        <h1>User Profile</h1>
        <button @click="$router.push('/dashboard')" class="btn-outline">
          Back to Dashboard
        </button>
      </div>
    </header>
    
    <main class="profile-main">
      <div class="profile-card">
        <div class="profile-info">
          <div class="avatar">
            {{ user?.username?.charAt(0).toUpperCase() }}
          </div>
          <div class="user-details">
            <h2>{{ user?.username }}</h2>
            <p>{{ user?.email }}</p>
            <span class="role-badge" :class="user?.role">{{ user?.role }}</span>
          </div>
        </div>
        
        <div class="profile-stats">
          <div class="stat-item">
            <span class="stat-value">{{ totalAttempts }}</span>
            <span class="stat-label">Total Attempts</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ averageScore }}%</span>
            <span class="stat-label">Average Score</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ bestScore }}%</span>
            <span class="stat-label">Best Score</span>
          </div>
        </div>
      </div>
      
      <div class="attempts-section">
        <h3>Quiz History</h3>
        <div v-if="attempts.length === 0" class="empty-state">
          <p>No quiz attempts yet.</p>
        </div>
        <div v-else class="attempts-grid">
          <div v-for="attempt in attempts" :key="attempt.id" class="attempt-card">
            <div class="attempt-header">
              <h4>{{ attempt.quiz_title }}</h4>
              <span class="attempt-date">{{ formatDate(attempt.completed_at) }}</span>
            </div>
            <div class="attempt-details">
              <div class="score-display">
                <span class="score" :class="getScoreClass(attempt.percentage)">
                  {{ attempt.percentage.toFixed(1) }}%
                </span>
                <span class="score-fraction">{{ attempt.score }}/{{ attempt.total_questions }}</span>
              </div>
              <div class="time-display">
                <span>Time: {{ formatTime(attempt.time_taken) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'UserProfile',
  data() {
    return {
      user: null,
      attempts: []
    }
  },
  computed: {
    totalAttempts() {
      return this.attempts.length
    },
    
    averageScore() {
      if (this.attempts.length === 0) return 0
      const total = this.attempts.reduce((sum, attempt) => sum + attempt.percentage, 0)
      return (total / this.attempts.length).toFixed(1)
    },
    
    bestScore() {
      if (this.attempts.length === 0) return 0
      return Math.max(...this.attempts.map(attempt => attempt.percentage)).toFixed(1)
    }
  },
  async created() {
    try {
      this.user = JSON.parse(localStorage.getItem('user'))
      await this.loadAttempts()
    } catch (error) {
      console.error('Error loading profile:', error)
    }
  },
  methods: {
    async loadAttempts() {
      try {
        const response = await api.getUserAttempts()
        this.attempts = response.data
      } catch (error) {
        console.error('Error loading attempts:', error)
      }
    },
    
    getScoreClass(percentage) {
      if (percentage >= 80) return 'score-excellent'
      if (percentage >= 60) return 'score-good'
      if (percentage >= 40) return 'score-fair'
      return 'score-poor'
    },
    
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }
  }
}
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f8fafc;
}

.profile-header {
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

.header-content h1 {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
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

.profile-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.profile-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  font-weight: 600;
}

.user-details h2 {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.user-details p {
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.role-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.role-badge.admin {
  background: #fef3c7;
  color: #d97706;
}

.role-badge.user {
  background: #dbeafe;
  color: #1e40af;
}

.profile-stats {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

.stat-item {
  text-align: center;
  flex: 1;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-value {
  display: block;
  font-size: 2rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
}

.attempts-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.attempts-section h3 {
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.attempts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.attempt-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  transition: transform 0.2s;
}

.attempt-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.attempt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.attempt-header h4 {
  color: #1f2937;
  font-size: 1rem;
  font-weight: 500;
}

.attempt-date {
  color: #6b7280;
  font-size: 0.875rem;
}

.attempt-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-display {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.score {
  font-size: 1.5rem;
  font-weight: 700;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.score-excellent {
  background: #dcfce7;
  color: #15803d;
}

.score-good {
  background: #fef3c7;
  color: #d97706;
}

.score-fair {
  background: #fed7aa;
  color: #ea580c;
}

.score-poor {
  background: #fee2e2;
  color: #dc2626;
}

.score-fraction {
  color: #6b7280;
  font-size: 0.875rem;
}

.time-display {
  color: #6b7280;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .profile-info {
    flex-direction: column;
    text-align: center;
  }
  
  .profile-stats {
    flex-direction: column;
    gap: 1rem;
  }
  
  .attempts-grid {
    grid-template-columns: 1fr;
  }
  
  .attempt-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .attempt-details {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>