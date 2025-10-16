<template>
  <div class="quiz-container">
    <div v-if="loading" class="loading">
      <p>Loading quiz...</p>
    </div>
    
    <div v-else-if="!quizStarted" class="quiz-intro">
      <div class="intro-card">
        <h1>{{ quiz.title }}</h1>
        <p class="quiz-description">{{ quiz.description }}</p>
        <div class="quiz-info">
          <div class="info-item">
            <span class="info-label">Questions:</span>
            <span>{{ quiz.total_questions }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Time Limit:</span>
            <span>{{ quiz.time_limit }} minutes</span>
          </div>
        </div>
        <button @click="startQuiz" class="btn-primary">
          Start Quiz
        </button>
      </div>
    </div>
    
    <div v-else class="quiz-active">
      <div class="quiz-header">
        <div class="quiz-progress">
          <span>Question {{ currentQuestion + 1 }} of {{ questions.length }}</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>
        <div class="quiz-timer">
          <span>⏱️ {{ formatTime(timeRemaining) }}</span>
        </div>
      </div>
      
      <div class="question-card">
        <h2>{{ questions[currentQuestion]?.question }}</h2>
        <div class="options">
          <div
            v-for="option in ['A', 'B', 'C', 'D']"
            :key="option"
            class="option"
            :class="{ selected: selectedAnswer === option }"
            @click="selectAnswer(option)"
          >
            <span class="option-letter">{{ option }}</span>
            <span class="option-text">{{ questions[currentQuestion]?.[`option_${option.toLowerCase()}`] }}</span>
          </div>
        </div>
        
        <div class="question-actions">
          <button
            v-if="currentQuestion > 0"
            @click="previousQuestion"
            class="btn-secondary"
          >
            Previous
          </button>
          <button
            v-if="currentQuestion < questions.length - 1"
            @click="nextQuestion"
            class="btn-primary"
            :disabled="!selectedAnswer"
          >
            Next
          </button>
          <button
            v-else
            @click="submitQuiz"
            class="btn-success"
            :disabled="!selectedAnswer"
          >
            Submit Quiz
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'

export default {
  name: 'Quiz',
  data() {
    return {
      loading: true,
      quiz: {},
      questions: [],
      currentQuestion: 0,
      selectedAnswer: null,
      answers: {},
      quizStarted: false,
      attemptId: null,
      timeRemaining: 0,
      timer: null,
      startTime: null
    }
  },
  computed: {
    progressPercentage() {
      return ((this.currentQuestion + 1) / this.questions.length) * 100
    }
  },
  async created() {
    await this.loadQuiz()
  },
  beforeUnmount() {
    if (this.timer) {
      clearInterval(this.timer)
    }
  },
  methods: {
    async loadQuiz() {
      try {
        const quizId = this.$route.params.id
        
        // Get quiz questions
        const response = await api.getQuizQuestions(quizId)
        this.questions = response.data
        
        if (this.questions.length === 0) {
          alert('This quiz has no questions.')
          this.$router.push('/dashboard')
          return
        }
        
        // Initialize quiz data
        this.quiz = {
          title: 'Quiz',
          description: 'Complete all questions to the best of your ability.',
          total_questions: this.questions.length,
          time_limit: 30 // Default time limit
        }
        
      } catch (error) {
        console.error('Error loading quiz:', error)
        alert('Failed to load quiz.')
        this.$router.push('/dashboard')
      } finally {
        this.loading = false
      }
    },
    
    async startQuiz() {
      try {
        const quizId = this.$route.params.id
        const response = await api.startQuiz(quizId)
        
        this.attemptId = response.data.attempt_id
        this.quiz.title = response.data.quiz_title
        this.quiz.time_limit = response.data.time_limit
        this.timeRemaining = this.quiz.time_limit * 60 // Convert to seconds
        this.startTime = new Date()
        
        this.quizStarted = true
        this.startTimer()
        
      } catch (error) {
        console.error('Error starting quiz:', error)
        alert('Failed to start quiz.')
      }
    },
    
    startTimer() {
      this.timer = setInterval(() => {
        this.timeRemaining--
        if (this.timeRemaining <= 0) {
          this.submitQuiz()
        }
      }, 1000)
    },
    
    selectAnswer(option) {
      this.selectedAnswer = option
      this.answers[this.questions[this.currentQuestion].id] = option
    },
    
    nextQuestion() {
      if (this.currentQuestion < this.questions.length - 1) {
        this.currentQuestion++
        this.selectedAnswer = this.answers[this.questions[this.currentQuestion].id] || null
      }
    },
    
    previousQuestion() {
      if (this.currentQuestion > 0) {
        this.currentQuestion--
        this.selectedAnswer = this.answers[this.questions[this.currentQuestion].id] || null
      }
    },
    
    async submitQuiz() {
      if (this.timer) {
        clearInterval(this.timer)
      }
      
      const timeTaken = Math.round((new Date() - this.startTime) / 1000)
      
      try {
        const response = await api.submitQuiz(this.attemptId, {
          answers: this.answers,
          time_taken: timeTaken
        })
        
        this.$router.push({
          name: 'QuizResult',
          params: { id: this.$route.params.id },
          query: {
            score: response.data.score,
            total: response.data.total_points,
            percentage: response.data.percentage,
            timeTaken: timeTaken
          }
        })
        
      } catch (error) {
        console.error('Error submitting quiz:', error)
        alert('Failed to submit quiz.')
      }
    },
    
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }
  }
}
</script>

<style scoped>
.quiz-container {
  min-height: 100vh;
  background: #f8fafc;
  padding: 2rem 1rem;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
  color: #6b7280;
}

.quiz-intro {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.intro-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 500px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.intro-card h1 {
  color: #1f2937;
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.quiz-description {
  color: #6b7280;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.quiz-info {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 500;
}

.quiz-active {
  max-width: 800px;
  margin: 0 auto;
}

.quiz-header {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.quiz-progress {
  flex: 1;
  margin-right: 2rem;
}

.progress-bar {
  background: #e5e7eb;
  height: 8px;
  border-radius: 4px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.progress-fill {
  background: #3b82f6;
  height: 100%;
  transition: width 0.3s ease;
}

.quiz-timer {
  color: #dc2626;
  font-weight: 600;
  font-size: 1.125rem;
}

.question-card {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.question-card h2 {
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 2rem;
  line-height: 1.4;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.option {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.option.selected {
  border-color: #3b82f6;
  background: #dbeafe;
}

.option-letter {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 50%;
  font-weight: 600;
  color: #374151;
}

.option.selected .option-letter {
  background: #3b82f6;
  color: white;
}

.option-text {
  flex: 1;
  color: #374151;
  font-size: 1rem;
  line-height: 1.5;
}

.question-actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.btn-primary, .btn-secondary, .btn-success {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background: #4b5563;
}

.btn-success {
  background: #10b981;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #059669;
}

.btn-primary:disabled,
.btn-success:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .quiz-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .quiz-progress {
    margin-right: 0;
    width: 100%;
  }
  
  .quiz-info {
    flex-direction: column;
    gap: 1rem;
  }
  
  .question-actions {
    flex-direction: column;
  }
}
</style>