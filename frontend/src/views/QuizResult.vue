<template>
  <div class="result-container">
    <div class="result-card">
      <div class="result-header">
        <div class="score-circle" :class="getScoreClass(percentage)">
          <span class="score-percentage">{{ percentage.toFixed(1) }}%</span>
        </div>
        <h1>Quiz Completed!</h1>
        <p class="score-text">{{ getScoreText(percentage) }}</p>
      </div>
      
      <div class="result-details">
        <div class="detail-item">
          <span class="detail-label">Score</span>
          <span class="detail-value">{{ score }} / {{ total }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Percentage</span>
          <span class="detail-value">{{ percentage.toFixed(1) }}%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Time Taken</span>
          <span class="detail-value">{{ formatTime(timeTaken) }}</span>
        </div>
      </div>
      
      <div class="result-actions">
        <button @click="$router.push('/dashboard')" class="btn-primary">
          Back to Dashboard
        </button>
        <button @click="retakeQuiz" class="btn-outline">
          Retake Quiz
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuizResult',
  data() {
    return {
      score: 0,
      total: 0,
      percentage: 0,
      timeTaken: 0
    }
  },
  created() {
    this.score = parseInt(this.$route.query.score) || 0
    this.total = parseInt(this.$route.query.total) || 0
    this.percentage = parseFloat(this.$route.query.percentage) || 0
    this.timeTaken = parseInt(this.$route.query.timeTaken) || 0
  },
  methods: {
    getScoreClass(percentage) {
      if (percentage >= 80) return 'score-excellent'
      if (percentage >= 60) return 'score-good'
      if (percentage >= 40) return 'score-fair'
      return 'score-poor'
    },
    
    getScoreText(percentage) {
      if (percentage >= 80) return 'Excellent! Outstanding performance!'
      if (percentage >= 60) return 'Good job! Well done!'
      if (percentage >= 40) return 'Fair attempt. Keep practicing!'
      return 'Need improvement. Try again!'
    },
    
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    
    retakeQuiz() {
      this.$router.push(`/quiz/${this.$route.params.id}`)
    }
  }
}
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.result-card {
  background: white;
  border-radius: 16px;
  padding: 3rem;
  max-width: 500px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.result-header {
  margin-bottom: 2rem;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  position: relative;
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: conic-gradient(
    from 0deg,
    var(--score-color) 0deg,
    var(--score-color) calc(var(--score-percentage) * 3.6deg),
    #e5e7eb calc(var(--score-percentage) * 3.6deg),
    #e5e7eb 360deg
  );
  padding: 8px;
  mask: radial-gradient(circle, transparent 40%, black 40%);
}

.score-excellent {
  --score-color: #10b981;
  --score-percentage: var(--percentage);
}

.score-good {
  --score-color: #f59e0b;
  --score-percentage: var(--percentage);
}

.score-fair {
  --score-color: #f97316;
  --score-percentage: var(--percentage);
}

.score-poor {
  --score-color: #ef4444;
  --score-percentage: var(--percentage);
}

.score-percentage {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
  z-index: 1;
}

.result-header h1 {
  color: #1f2937;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.score-text {
  color: #6b7280;
  font-size: 1.125rem;
  font-weight: 500;
}

.result-details {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  color: #6b7280;
  font-weight: 500;
}

.detail-value {
  color: #1f2937;
  font-weight: 600;
}

.result-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

.btn-outline {
  background: transparent;
  color: #3b82f6;
  border: 2px solid #3b82f6;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-outline:hover {
  background: #3b82f6;
  color: white;
}

@media (max-width: 768px) {
  .result-card {
    padding: 2rem;
  }
  
  .result-actions {
    flex-direction: column;
  }
}
</style>