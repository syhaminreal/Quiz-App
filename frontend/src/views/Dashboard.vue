<template>
  <div class="dashboard-container">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="header-left">
          <h1>Quiz Dashboard</h1>
          <div class="breadcrumb" v-if="breadcrumb.length > 0">
            <span 
              v-for="(item, index) in breadcrumb" 
              :key="index"
              class="breadcrumb-item"
              :class="{ active: index === breadcrumb.length - 1 }"
              @click="navigateToBreadcrumb(index)"
            >
              {{ item.name }}
              <span v-if="index < breadcrumb.length - 1" class="breadcrumb-separator">></span>
            </span>
          </div>
        </div>
        <div class="header-right">
          <button @click="$router.push('/profile')" class="btn-outline">
            Profile
          </button>
          <button @click="logout" class="btn-secondary">
            Logout
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="dashboard-main">
      <!-- Subjects View -->
      <div v-if="currentView === 'subjects'" class="content-section">
        <div class="section-header">
          <h2>Select a Subject</h2>
          <div class="search-bar">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search subjects..."
              class="search-input"
            />
          </div>
        </div>
        
        <div v-if="loading" class="loading">Loading subjects...</div>
        
        <div v-else-if="filteredSubjects.length === 0" class="empty-state">
          <p>No subjects available.</p>
        </div>
        
        <div v-else class="subjects-grid">
          <div
            v-for="subject in filteredSubjects"
            :key="subject.id"
            class="subject-card"
            @click="selectSubject(subject)"
          >
            <div class="card-header">
              <h3>{{ subject.name }}</h3>
              <span class="chapter-count">{{ subject.chapter_count }} chapters</span>
            </div>
            <p class="card-description">{{ subject.description || 'No description available' }}</p>
          </div>
        </div>
      </div>

      <!-- Chapters View -->
      <div v-if="currentView === 'chapters'" class="content-section">
        <div class="section-header">
          <h2>Chapters in {{ selectedSubject?.name }}</h2>
          <div class="search-bar">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search chapters..."
              class="search-input"
            />
          </div>
        </div>
        
        <div v-if="loading" class="loading">Loading chapters...</div>
        
        <div v-else-if="filteredChapters.length === 0" class="empty-state">
          <p>No chapters available in this subject.</p>
        </div>
        
        <div v-else class="chapters-grid">
          <div
            v-for="chapter in filteredChapters"
            :key="chapter.id"
            class="chapter-card"
            @click="selectChapter(chapter)"
          >
            <div class="card-header">
              <h3>{{ chapter.name }}</h3>
              <span class="quiz-count">{{ chapter.quiz_count }} quizzes</span>
            </div>
            <p class="card-description">{{ chapter.description || 'No description available' }}</p>
          </div>
        </div>
      </div>

      <!-- Quizzes View -->
      <div v-if="currentView === 'quizzes'" class="content-section">
        <div class="section-header">
          <h2>Quizzes in {{ selectedChapter?.name }}</h2>
          <div class="search-bar">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search quizzes..."
              class="search-input"
            />
          </div>
        </div>
        
        <div v-if="loading" class="loading">Loading quizzes...</div>
        
        <div v-else-if="filteredQuizzes.length === 0" class="empty-state">
          <p>No quizzes available in this chapter.</p>
        </div>
        
        <div v-else class="quizzes-grid">
          <div
            v-for="quiz in filteredQuizzes"
            :key="quiz.id"
            class="quiz-card"
          >
            <div class="card-header">
              <h3>{{ quiz.title }}</h3>
              <span class="question-count">{{ quiz.question_count }} questions</span>
            </div>
            <p class="card-description">{{ quiz.description || 'No description available' }}</p>
            <div class="quiz-info">
              <span class="time-limit">⏱️ {{ quiz.time_limit }} minutes</span>
            </div>
            <div class="quiz-actions">
              <button @click="startQuiz(quiz)" class="btn-primary">
                Take Quiz
              </button>
              <button @click="viewQuizAttempts(quiz)" class="btn-outline">
                View Attempts
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Analytics Section -->
      <div v-if="currentView === 'subjects'" class="content-section">
        <div class="section-header">
          <h2>Your Performance Analytics</h2>
          <button @click="exportPerformance" class="btn-outline">
            📊 Export Report
          </button>
        </div>
        
        <div v-if="recentAttempts.length === 0" class="empty-state">
          <p>No quiz attempts yet. Start taking quizzes to see your analytics!</p>
        </div>
        
        <div v-else class="analytics-container">
          <!-- Summary Cards -->
          <div class="summary-cards">
            <div class="summary-card">
              <div class="card-icon">📝</div>
              <div class="card-content">
                <h3>{{ totalAttempts }}</h3>
                <p>Total Attempts</p>
              </div>
            </div>
            <div class="summary-card">
              <div class="card-icon">📈</div>
              <div class="card-content">
                <h3>{{ averageScore }}%</h3>
                <p>Average Score</p>
              </div>
            </div>
            <div class="summary-card">
              <div class="card-icon">🏆</div>
              <div class="card-content">
                <h3>{{ bestScore }}%</h3>
                <p>Best Score</p>
              </div>
            </div>
            <div class="summary-card">
              <div class="card-icon">⏱️</div>
              <div class="card-content">
                <h3>{{ averageTime }}</h3>
                <p>Avg Time</p>
              </div>
            </div>
          </div>

          <!-- Charts -->
          <div class="charts-grid">
            <div class="chart-card">
              <h3>Performance Over Time</h3>
              <LineChart
                :data="performanceChartData"
                :labels="performanceChartLabels"
                title="Your Quiz Performance Trend"
              />
            </div>
            
            <div class="chart-card">
              <h3>Quiz Scores Distribution</h3>
              <BarChart
                :data="quizScoresData"
                :labels="quizScoresLabels"
                title="Scores by Quiz"
                color="#10b981"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Attempts Section -->
      <div v-if="currentView === 'subjects'" class="content-section">
        <div class="section-header">
          <h2>Recent Quiz Attempts</h2>
        </div>
        
        <div v-if="recentAttempts.length === 0" class="empty-state">
          <p>No quiz attempts yet. Start taking quizzes!</p>
        </div>
        
        <div v-else class="attempts-list">
          <div
            v-for="attempt in recentAttempts.slice(0, 8)"
            :key="attempt.id"
            class="attempt-item"
          >
            <div class="attempt-info">
              <h4>{{ attempt.quiz_title }}</h4>
              <p class="attempt-date">{{ formatDate(attempt.completed_at) }}</p>
            </div>
            <div class="attempt-score">
              <span class="score" :class="getScoreClass(attempt.percentage)">
                {{ attempt.percentage.toFixed(1) }}%
              </span>
              <span class="score-details">{{ attempt.score }}/{{ attempt.total_questions }}</span>
              <span class="time-taken">{{ formatTime(attempt.time_taken) }}</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Quiz Attempts Modal -->
    <div v-if="showAttemptsModal" class="modal-overlay" @click="closeAttemptsModal">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>Your Attempts: {{ selectedQuizForAttempts?.title }}</h3>
          <button @click="closeAttemptsModal" class="close-btn">&times;</button>
        </div>
        
        <div class="modal-body">
          <div v-if="loadingAttempts" class="loading">Loading attempts...</div>
          
          <div v-else-if="quizAttempts.length === 0" class="empty-state">
            <p>You haven't attempted this quiz yet.</p>
          </div>
          
          <div v-else class="attempts-table-container">
            <table class="attempts-table">
              <thead>
                <tr>
                  <th>Attempt #</th>
                  <th>Score</th>
                  <th>Percentage</th>
                  <th>Time Taken</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(attempt, index) in quizAttempts" :key="attempt.id">
                  <td>{{ index + 1 }}</td>
                  <td>{{ attempt.score }}/{{ attempt.total_questions }}</td>
                  <td>
                    <span class="score-badge" :class="getScoreClass(attempt.percentage)">
                      {{ attempt.percentage.toFixed(1) }}%
                    </span>
                  </td>
                  <td>{{ formatTime(attempt.time_taken) }}</td>
                  <td>{{ formatDateTime(attempt.completed_at) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeAttemptsModal" class="btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../services/api'
import BarChart from '../components/charts/BarChart.vue'
import LineChart from '../components/charts/LineChart.vue'
import PDFExporter from '../utils/pdfExport'

export default {
  name: 'Dashboard',
  components: {
    BarChart,
    LineChart
  },
  data() {
    return {
      currentView: 'subjects', // subjects, chapters, quizzes
      loading: false,
      searchQuery: '',
      
      // Data
      subjects: [],
      chapters: [],
      quizzes: [],
      recentAttempts: [],
      
      // Selected items
      selectedSubject: null,
      selectedChapter: null,
      
      // Breadcrumb
      breadcrumb: [],
      
      // Quiz attempts modal
      showAttemptsModal: false,
      selectedQuizForAttempts: null,
      quizAttempts: [],
      loadingAttempts: false
    }
  },
  computed: {
    filteredSubjects() {
      if (!this.searchQuery) return this.subjects
      return this.subjects.filter(subject =>
        subject.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        (subject.description && subject.description.toLowerCase().includes(this.searchQuery.toLowerCase()))
      )
    },
    
    filteredChapters() {
      if (!this.searchQuery) return this.chapters
      return this.chapters.filter(chapter =>
        chapter.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        (chapter.description && chapter.description.toLowerCase().includes(this.searchQuery.toLowerCase()))
      )
    },
    
    filteredQuizzes() {
      if (!this.searchQuery) return this.quizzes
      return this.quizzes.filter(quiz =>
        quiz.title.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
        (quiz.description && quiz.description.toLowerCase().includes(this.searchQuery.toLowerCase()))
      )
    },
    
    totalAttempts() {
      return this.recentAttempts.length
    },
    
    averageScore() {
      if (this.recentAttempts.length === 0) return 0
      const total = this.recentAttempts.reduce((sum, attempt) => sum + attempt.percentage, 0)
      return (total / this.recentAttempts.length).toFixed(1)
    },
    
    bestScore() {
      if (this.recentAttempts.length === 0) return 0
      return Math.max(...this.recentAttempts.map(attempt => attempt.percentage)).toFixed(1)
    },
    
    averageTime() {
      if (this.recentAttempts.length === 0) return '0:00'
      const totalSeconds = this.recentAttempts.reduce((sum, attempt) => sum + attempt.time_taken, 0)
      const avgSeconds = Math.round(totalSeconds / this.recentAttempts.length)
      return this.formatTime(avgSeconds)
    },
    
    performanceChartData() {
      return this.recentAttempts.slice(-10).reverse().map(attempt => attempt.percentage)
    },
    
    performanceChartLabels() {
      return this.recentAttempts.slice(-10).map((attempt, index) => `Attempt ${index + 1}`)
    },
    
    quizScoresData() {
      // Group attempts by quiz and get average score
      const quizGroups = {}
      this.recentAttempts.forEach(attempt => {
        if (!quizGroups[attempt.quiz_title]) {
          quizGroups[attempt.quiz_title] = []
        }
        quizGroups[attempt.quiz_title].push(attempt.percentage)
      })
      
      return Object.values(quizGroups).map(scores => 
        (scores.reduce((sum, score) => sum + score, 0) / scores.length).toFixed(1)
      )
    },
    
    quizScoresLabels() {
      const quizGroups = {}
      this.recentAttempts.forEach(attempt => {
        if (!quizGroups[attempt.quiz_title]) {
          quizGroups[attempt.quiz_title] = []
        }
        quizGroups[attempt.quiz_title].push(attempt.percentage)
      })
      
      return Object.keys(quizGroups).map(title => 
        title.length > 15 ? title.substring(0, 15) + '...' : title
      )
    }
  },
  async created() {
    await this.loadSubjects()
    await this.loadRecentAttempts()
  },
  methods: {
    async loadSubjects() {
      try {
        this.loading = true
        const response = await api.getSubjects()
        this.subjects = response.data
      } catch (error) {
        console.error('Error loading subjects:', error)
        alert('Failed to load subjects')
      } finally {
        this.loading = false
      }
    },
    
    async loadChapters(subjectId) {
      try {
        this.loading = true
        const response = await api.getChapters(subjectId)
        this.chapters = response.data
      } catch (error) {
        console.error('Error loading chapters:', error)
        alert('Failed to load chapters')
      } finally {
        this.loading = false
      }
    },
    
    async loadQuizzes(chapterId) {
      try {
        this.loading = true
        const response = await api.getQuizzes(chapterId)
        this.quizzes = response.data
      } catch (error) {
        console.error('Error loading quizzes:', error)
        alert('Failed to load quizzes')
      } finally {
        this.loading = false
      }
    },
    
    async loadRecentAttempts() {
      try {
        const response = await api.getUserAttempts()
        this.recentAttempts = response.data
      } catch (error) {
        console.error('Error loading recent attempts:', error)
      }
    },
    
    async loadQuizAttempts(quizId) {
      try {
        this.loadingAttempts = true
        const response = await api.getQuizAttempts(quizId)
        this.quizAttempts = response.data
      } catch (error) {
        console.error('Error loading quiz attempts:', error)
        alert('Failed to load quiz attempts')
      } finally {
        this.loadingAttempts = false
      }
    },
    
    selectSubject(subject) {
      this.selectedSubject = subject
      this.currentView = 'chapters'
      this.searchQuery = ''
      this.breadcrumb = [
        { name: 'Subjects', view: 'subjects' },
        { name: subject.name, view: 'chapters' }
      ]
      this.loadChapters(subject.id)
    },
    
    selectChapter(chapter) {
      this.selectedChapter = chapter
      this.currentView = 'quizzes'
      this.searchQuery = ''
      this.breadcrumb = [
        { name: 'Subjects', view: 'subjects' },
        { name: this.selectedSubject.name, view: 'chapters' },
        { name: chapter.name, view: 'quizzes' }
      ]
      this.loadQuizzes(chapter.id)
    },
    
    navigateToBreadcrumb(index) {
      const item = this.breadcrumb[index]
      this.searchQuery = ''
      
      if (item.view === 'subjects') {
        this.currentView = 'subjects'
        this.breadcrumb = []
        this.selectedSubject = null
        this.selectedChapter = null
      } else if (item.view === 'chapters') {
        this.currentView = 'chapters'
        this.breadcrumb = this.breadcrumb.slice(0, 2)
        this.selectedChapter = null
      }
    },
    
    startQuiz(quiz) {
      this.$router.push(`/quiz/${quiz.id}`)
    },
    
    async viewQuizAttempts(quiz) {
      this.selectedQuizForAttempts = quiz
      this.showAttemptsModal = true
      await this.loadQuizAttempts(quiz.id)
    },
    
    closeAttemptsModal() {
      this.showAttemptsModal = false
      this.selectedQuizForAttempts = null
      this.quizAttempts = []
    },
    
    exportPerformance() {
      const user = JSON.parse(localStorage.getItem('user'))
      const exporter = new PDFExporter()
      exporter.exportUserPerformance(user, this.recentAttempts, false)
    },
    
    getScoreClass(percentage) {
      if (percentage >= 80) return 'score-excellent'
      if (percentage >= 60) return 'score-good'
      if (percentage >= 40) return 'score-fair'
      return 'score-poor'
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },
    
    formatDateTime(dateString) {
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('userRole')
      this.$router.push('/login')
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  min-height: 100vh;
  background: #f8fafc;
}

.dashboard-header {
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
  margin-bottom: 0.5rem;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.breadcrumb-item {
  cursor: pointer;
  transition: color 0.2s;
}

.breadcrumb-item:hover:not(.active) {
  color: #3b82f6;
}

.breadcrumb-item.active {
  color: #1f2937;
  font-weight: 500;
}

.breadcrumb-separator {
  margin: 0 0.5rem;
  color: #9ca3af;
}

.header-right {
  display: flex;
  gap: 1rem;
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

.btn-secondary {
  padding: 0.5rem 1rem;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background: #4b5563;
}

.dashboard-main {
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

.search-bar {
  flex: 1;
  max-width: 300px;
  margin-left: 2rem;
}

.search-input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #6b7280;
}

.subjects-grid,
.chapters-grid,
.quizzes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.subject-card,
.chapter-card,
.quiz-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.subject-card:hover,
.chapter-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.quiz-card {
  cursor: default;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h3 {
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 500;
}

.chapter-count,
.quiz-count,
.question-count {
  background: #dbeafe;
  color: #1e40af;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.card-description {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: 1rem;
}

.quiz-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.time-limit {
  color: #6b7280;
  font-size: 0.875rem;
}

.quiz-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background: #2563eb;
}

/* Analytics Styles */
.analytics-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.summary-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  font-size: 2rem;
}

.card-content h3 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.card-content p {
  font-size: 0.875rem;
  opacity: 0.9;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.chart-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.chart-card h3 {
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.attempts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.attempt-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: transform 0.2s;
}

.attempt-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.attempt-info h4 {
  color: #1f2937;
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.attempt-date {
  color: #6b7280;
  font-size: 0.875rem;
}

.attempt-score {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.score {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
}

.score-details {
  color: #6b7280;
  font-size: 0.875rem;
}

.time-taken {
  color: #6b7280;
  font-size: 0.75rem;
}

.score-excellent {
  color: #059669;
}

.score-good {
  color: #d97706;
}

.score-fair {
  color: #ea580c;
}

.score-poor {
  color: #dc2626;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.large-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #374151;
}

.modal-body {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.attempts-table-container {
  overflow-x: auto;
}

.attempts-table {
  width: 100%;
  border-collapse: collapse;
}

.attempts-table th,
.attempts-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.attempts-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #374151;
}

.score-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.score-badge.score-excellent {
  background: #dcfce7;
  color: #15803d;
}

.score-badge.score-good {
  background: #fef3c7;
  color: #d97706;
}

.score-badge.score-fair {
  background: #fed7aa;
  color: #ea580c;
}

.score-badge.score-poor {
  background: #fee2e2;
  color: #dc2626;
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
  
  .search-bar {
    margin-left: 0;
    max-width: none;
  }
  
  .subjects-grid,
  .chapters-grid,
  .quizzes-grid {
    grid-template-columns: 1fr;
  }
  
  .quiz-actions {
    flex-direction: column;
  }
  
  .attempt-item {
    flex-direction: column;
    gap: 1rem;
  }
  
  .attempt-score {
    text-align: left;
  }
  
  .summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>