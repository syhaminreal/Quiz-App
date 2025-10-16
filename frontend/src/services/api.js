import axios from "axios";

const API_BASE_URL = "http://localhost:5000/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      localStorage.removeItem("userRole");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default {
  // Auth endpoints
  login: (credentials) => api.post("/login", credentials),
  register: (userData) => api.post("/register", userData),
  getProfile: () => api.get("/profile"),

  // Subject endpoints
  getSubjects: () => api.get("/subjects"),
  createSubject: (subjectData) => api.post("/subjects", subjectData),
  deleteSubject: (subjectId) => api.delete(`/subjects/${subjectId}`),

  // Chapter endpoints
  getChapters: (subjectId) => api.get(`/subjects/${subjectId}/chapters`),
  createChapter: (chapterData) => api.post("/chapters", chapterData),
  deleteChapter: (chapterId) => api.delete(`/chapters/${chapterId}`),

  // Quiz endpoints
  getQuizzes: (chapterId) => api.get(`/chapters/${chapterId}/quizzes`),
  createQuiz: (quizData) => api.post("/quizzes", quizData),
  updateQuiz: (quizId, quizData) => api.put(`/quizzes/${quizId}`, quizData),
  deleteQuiz: (quizId) => api.delete(`/quizzes/${quizId}`),
  getQuizQuestions: (quizId) => api.get(`/quizzes/${quizId}/questions`),
  addQuestion: (quizId, questionData) =>
    api.post(`/quizzes/${quizId}/questions`, questionData),
  updateQuestion: (questionId, questionData) =>
    api.put(`/questions/${questionId}`, questionData),
  deleteQuestion: (questionId) => api.delete(`/questions/${questionId}`),
  startQuiz: (quizId) => api.post(`/quizzes/${quizId}/start`),
  submitQuiz: (attemptId, submissionData) =>
    api.post(`/attempts/${attemptId}/submit`, submissionData),
  getQuizAttempts: (quizId) => api.get(`/quizzes/${quizId}/attempts`),

  // User endpoints
  getUserAttempts: () => api.get("/user/attempts"),

  // Admin endpoints
  getUsers: () => api.get("/admin/users"),
  addUser: (userData) => api.post("/admin/users", userData),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  updateUser: (userId, userData) => api.put(`/admin/users/${userId}`, userData),
  getReports: () => api.get("/admin/reports"),

  // Job management endpoints
  testUserReminders: () => api.post("/admin/jobs/test-reminders"),
  testAdminReport: () => api.post("/admin/jobs/test-admin-report"),
  testCleanup: () => api.post("/admin/jobs/test-cleanup"),
  getInactiveUsers: () => api.get("/admin/jobs/inactive-users"),
  getDailyStats: () => api.get("/admin/jobs/daily-stats"),
};
