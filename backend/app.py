from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
from datetime import datetime, timedelta
import bcrypt
import os
from functools import wraps
from dotenv import load_dotenv
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import joinedload

# Import models and database
from models import db, User, Subject, Chapter, Quiz, Question, QuizAttempt, UserAnswer

# Import the job scheduler
from jobs import job_scheduler, test_user_reminders, test_admin_report, test_weekly_cleanup, test_get_inactive_users, test_get_daily_stats

load_dotenv()

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)

# CORS configuration - Fix CORS error
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'message': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'message': 'Authorization token is required'}), 401

# Database initialization
def init_db():
    with app.app_context():
        # Run migration first if needed
        try:
            from migrate_db import migrate_database
            migrate_database()
        except Exception as e:
            print(f"Migration warning: {str(e)}")
        
        db.create_all()
        
        # Check if admin user exists
        admin_user = User.query.filter_by(role='admin').first()
        
        if not admin_user:
            admin_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            admin_user = User(
                username='admin',
                email='admin@quizapp.com',
                password_hash=admin_password.decode('utf-8'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Created default admin user: admin/admin123")
        
        # Create sample data if tables are empty
        quiz_count = Quiz.query.count()
        
        if quiz_count == 0:
            # Create sample quizzes
            # Create sample subjects
            sample_subjects = [
                ('Mathematics', 'Mathematical concepts and problem solving'),
                ('Science', 'Physics, Chemistry, and Biology'),
                ('History', 'World history and historical events'),
                ('General Knowledge', 'Miscellaneous topics and current affairs')
            ]
            
            for name, description in sample_subjects:
                subject = Subject(
                    name=name,
                    description=description,
                    created_by=admin_user.id
                )
                db.session.add(subject)
            
            db.session.commit()
            
            # Create sample chapters
            math_subject = Subject.query.filter_by(name='Mathematics').first()
            if math_subject:
                chapter = Chapter(
                    name='Basic Arithmetic',
                    description='Addition, subtraction, multiplication, and division',
                    subject_id=math_subject.id,
                    created_by=admin_user.id
                )
                db.session.add(chapter)
                db.session.commit()
                
                # Create sample quiz
                quiz = Quiz(
                    title='Basic Math Quiz',
                    description='Test your basic arithmetic skills',
                    chapter_id=chapter.id,
                    time_limit=20,
                    created_by=admin_user.id
                )
                db.session.add(quiz)
                db.session.commit()
                
                # Add sample questions
                sample_questions = [
                    ('What is 5 + 3?', '6', '7', '8', '9', 'C'),
                    ('What is 12 - 4?', '6', '7', '8', '9', 'C'),
                    ('What is 6 × 7?', '40', '41', '42', '43', 'C'),
                    ('What is 24 ÷ 6?', '3', '4', '5', '6', 'B'),
                    ('What is 15 + 25?', '35', '40', '45', '50', 'B')
                ]
                
                for question_text, opt_a, opt_b, opt_c, opt_d, correct in sample_questions:
                    question = Question(
                        quiz_id=quiz.id,
                        question=question_text,
                        option_a=opt_a,
                        option_b=opt_b,
                        option_c=opt_c,
                        option_d=opt_d,
                        correct_answer=correct
                    )
                    db.session.add(question)
                
                db.session.commit()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # First check if we have a valid JWT token
            from flask_jwt_extended import verify_jwt_in_request
            verify_jwt_in_request()
            
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({'message': 'Invalid token identity'}), 401
                
            user = User.query.get(int(current_user_id))
            
            if not user or user.role != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Admin auth error: {str(e)}")
            return jsonify({'message': 'Authentication error', 'error': str(e)}), 401
    return decorated_function

# Error handlers
@app.errorhandler(422)
def handle_unprocessable_entity(e):
    return jsonify({'message': 'Unprocessable entity', 'error': str(e)}), 422

@app.errorhandler(500)
def handle_internal_error(e):
    return jsonify({'message': 'Internal server error', 'error': str(e)}), 500

# Auth routes
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'message': 'All fields are required'}), 400
        
        # Check if user exists
        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash.decode('utf-8')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {str(e)}")
        return jsonify({'message': 'Registration failed', 'error': str(e)}), 500

# Subject routes
@app.route('/api/subjects', methods=['GET'])
@jwt_required()
def get_subjects():
    try:
        subjects = db.session.query(
            Subject.id,
            Subject.name,
            Subject.description,
            Subject.is_active,
            func.count(Chapter.id).label('chapter_count')
        ).outerjoin(Chapter).filter(
            Subject.is_active == True
        ).group_by(Subject.id).order_by(desc(Subject.created_at)).all()
        
        subject_list = []
        for subject in subjects:
            subject_list.append({
                'id': subject.id,
                'name': subject.name,
                'description': subject.description,
                'is_active': subject.is_active,
                'chapter_count': subject.chapter_count
            })
        
        return jsonify(subject_list), 200
        
    except Exception as e:
        print(f"Get subjects error: {str(e)}")
        return jsonify({'message': 'Failed to get subjects', 'error': str(e)}), 422

@app.route('/api/subjects', methods=['POST'])
@admin_required
def create_subject():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        name = data.get('name')
        description = data.get('description')
        current_user_id = int(get_jwt_identity())
        
        if not name:
            return jsonify({'message': 'Name is required'}), 400
        
        # Check if subject already exists
        existing_subject = Subject.query.filter_by(name=name).first()
        if existing_subject:
            return jsonify({'message': 'Subject with this name already exists'}), 400
        
        subject = Subject(
            name=name,
            description=description,
            created_by=current_user_id
        )
        
        db.session.add(subject)
        db.session.commit()
        
        return jsonify({'message': 'Subject created successfully', 'subject_id': subject.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create subject error: {str(e)}")
        return jsonify({'message': 'Failed to create subject', 'error': str(e)}), 500

@app.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
@admin_required
def delete_subject(subject_id):
    try:
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'message': 'Subject not found'}), 404
            
        # Delete all associated data in correct order
        chapters = Chapter.query.filter_by(subject_id=subject_id).all()
        for chapter in chapters:
            quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
            for quiz in quizzes:
                # Delete user answers for all questions in this quiz
                questions = Question.query.filter_by(quiz_id=quiz.id).all()
                for question in questions:
                    UserAnswer.query.filter_by(question_id=question.id).delete()
                
                # Delete all questions in this quiz
                Question.query.filter_by(quiz_id=quiz.id).delete()
                
                # Delete all quiz attempts for this quiz
                QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
                
                # Delete the quiz
                db.session.delete(quiz)
            
            # Delete the chapter
            db.session.delete(chapter)
        
        # Finally delete the subject
        db.session.delete(subject)
        db.session.commit()
        
        return jsonify({'message': 'Subject deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete subject error: {str(e)}")
        return jsonify({'message': 'Failed to delete subject', 'error': str(e)}), 500

# Chapter routes
@app.route('/api/subjects/<int:subject_id>/chapters', methods=['GET'])
@jwt_required()
def get_chapters(subject_id):
    try:
        chapters = db.session.query(
            Chapter.id,
            Chapter.name,
            Chapter.description,
            Chapter.is_active,
            func.count(Quiz.id).label('quiz_count')
        ).outerjoin(Quiz).filter(
            and_(Chapter.subject_id == subject_id, Chapter.is_active == True)
        ).group_by(Chapter.id).order_by(desc(Chapter.created_at)).all()
        
        chapter_list = []
        for chapter in chapters:
            chapter_list.append({
                'id': chapter.id,
                'name': chapter.name,
                'description': chapter.description,
                'is_active': chapter.is_active,
                'quiz_count': chapter.quiz_count
            })
        
        return jsonify(chapter_list), 200
        
    except Exception as e:
        print(f"Get chapters error: {str(e)}")
        return jsonify({'message': 'Failed to get chapters', 'error': str(e)}), 422

@app.route('/api/chapters', methods=['POST'])
@admin_required
def create_chapter():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        name = data.get('name')
        description = data.get('description')
        subject_id = data.get('subject_id')
        current_user_id = int(get_jwt_identity())
        
        if not all([name, subject_id]):
            return jsonify({'message': 'Name and subject are required'}), 400
        
        # Check if subject exists
        subject = Subject.query.get(subject_id)
        if not subject:
            return jsonify({'message': 'Subject not found'}), 404
        
        chapter = Chapter(
            name=name,
            description=description,
            subject_id=subject_id,
            created_by=current_user_id
        )
        
        db.session.add(chapter)
        db.session.commit()
        
        return jsonify({'message': 'Chapter created successfully', 'chapter_id': chapter.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create chapter error: {str(e)}")
        return jsonify({'message': 'Failed to create chapter', 'error': str(e)}), 500

@app.route('/api/chapters/<int:chapter_id>', methods=['DELETE'])
@admin_required
def delete_chapter(chapter_id):
    try:
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'message': 'Chapter not found'}), 404
            
        # Delete all associated data in correct order
        quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
        for quiz in quizzes:
            # Delete user answers for all questions in this quiz
            questions = Question.query.filter_by(quiz_id=quiz.id).all()
            for question in questions:
                UserAnswer.query.filter_by(question_id=question.id).delete()
            
            # Delete all questions in this quiz
            Question.query.filter_by(quiz_id=quiz.id).delete()
            
            # Delete all quiz attempts for this quiz
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            
            # Delete the quiz
            db.session.delete(quiz)
        
        # Finally delete the chapter
        db.session.delete(chapter)
        db.session.commit()
        
        return jsonify({'message': 'Chapter deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete chapter error: {str(e)}")
        return jsonify({'message': 'Failed to delete chapter', 'error': str(e)}), 500

# Quiz routes (updated)
@app.route('/api/chapters/<int:chapter_id>/quizzes', methods=['GET'])
@jwt_required()
def get_chapter_quizzes(chapter_id):
    try:
        quizzes = db.session.query(
            Quiz.id,
            Quiz.title,
            Quiz.description,
            Quiz.time_limit,
            Quiz.is_active,
            func.count(Question.id).label('question_count')
        ).outerjoin(Question).filter(
            and_(Quiz.chapter_id == chapter_id, Quiz.is_active == True)
        ).group_by(Quiz.id).order_by(desc(Quiz.created_at)).all()
        
        quiz_list = []
        for quiz in quizzes:
            quiz_list.append({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'time_limit': quiz.time_limit,
                'is_active': quiz.is_active,
                'question_count': quiz.question_count
            })
        
        return jsonify(quiz_list), 200
        
    except Exception as e:
        print(f"Get chapter quizzes error: {str(e)}")
        return jsonify({'message': 'Failed to get quizzes', 'error': str(e)}), 422

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'message': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Create token with user ID as string to avoid JWT issues
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'message': 'Login failed', 'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }), 200
        
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return jsonify({'message': 'Failed to get profile', 'error': str(e)}), 422

# Quiz routes
@app.route('/api/quizzes', methods=['GET'])
@jwt_required()
def get_quizzes():
    try:
        quizzes = db.session.query(
            Quiz.id,
            Quiz.title,
            Quiz.description,
            Quiz.time_limit,
            Quiz.is_active,
            func.count(Question.id).label('question_count')
        ).outerjoin(Question).filter(
            Quiz.is_active == True
        ).group_by(Quiz.id).order_by(desc(Quiz.created_at)).all()
        
        quiz_list = []
        for quiz in quizzes:
            quiz_list.append({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'time_limit': quiz.time_limit,
                'is_active': quiz.is_active,
                'question_count': quiz.question_count
            })
        
        return jsonify(quiz_list), 200
        
    except Exception as e:
        print(f"Get quizzes error: {str(e)}")
        return jsonify({'message': 'Failed to get quizzes', 'error': str(e)}), 422

@app.route('/api/quizzes', methods=['POST'])
@admin_required
def create_quiz():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        title = data.get('title')
        description = data.get('description')
        time_limit = data.get('time_limit', 30)
        chapter_id = data.get('chapter_id')
        current_user_id = int(get_jwt_identity())
        
        if not all([title, chapter_id]):
            return jsonify({'message': 'Title and chapter are required'}), 400
        
        # Check if chapter exists
        chapter = Chapter.query.get(chapter_id)
        if not chapter:
            return jsonify({'message': 'Chapter not found'}), 404
        
        quiz = Quiz(
            title=title,
            description=description,
            time_limit=time_limit,
            chapter_id=chapter_id,
            created_by=current_user_id
        )
        
        db.session.add(quiz)
        db.session.commit()
        
        return jsonify({'message': 'Quiz created successfully', 'quiz_id': quiz.id}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Create quiz error: {str(e)}")
        return jsonify({'message': 'Failed to create quiz', 'error': str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>', methods=['PUT'])
@admin_required
def update_quiz(quiz_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'message': 'Quiz not found'}), 404
            
        # Update quiz fields
        if 'title' in data:
            quiz.title = data['title']
        if 'description' in data:
            quiz.description = data['description']
        if 'time_limit' in data:
            quiz.time_limit = data['time_limit']
        if 'is_active' in data:
            quiz.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({'message': 'Quiz updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update quiz error: {str(e)}")
        return jsonify({'message': 'Failed to update quiz', 'error': str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/questions', methods=['GET'])
@jwt_required()
def get_quiz_questions(quiz_id):
    try:
        questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id).all()
        
        question_list = []
        for question in questions:
            question_list.append({
                'id': question.id,
                'question': question.question,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'points': question.points
            })
        
        return jsonify(question_list), 200
        
    except Exception as e:
        print(f"Get quiz questions error: {str(e)}")
        return jsonify({'message': 'Failed to get questions', 'error': str(e)}), 422

@app.route('/api/quizzes/<int:quiz_id>/questions', methods=['POST'])
@admin_required
def add_question(quiz_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        question_text = data.get('question')
        option_a = data.get('option_a')
        option_b = data.get('option_b')
        option_c = data.get('option_c')
        option_d = data.get('option_d')
        correct_answer = data.get('correct_answer')
        points = data.get('points', 1)
        
        if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
            return jsonify({'message': 'All fields are required'}), 400
        
        if correct_answer not in ['A', 'B', 'C', 'D']:
            return jsonify({'message': 'Correct answer must be A, B, C, or D'}), 400
        
        question = Question(
            quiz_id=quiz_id,
            question=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            points=points
        )
        
        db.session.add(question)
        db.session.commit()
        
        return jsonify({'message': 'Question added successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Add question error: {str(e)}")
        return jsonify({'message': 'Failed to add question', 'error': str(e)}), 500

@app.route('/api/questions/<int:question_id>', methods=['PUT'])
@admin_required
def update_question(question_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'message': 'Question not found'}), 404
            
        # Update question fields
        if 'question' in data:
            question.question = data['question']
        if 'option_a' in data:
            question.option_a = data['option_a']
        if 'option_b' in data:
            question.option_b = data['option_b']
        if 'option_c' in data:
            question.option_c = data['option_c']
        if 'option_d' in data:
            question.option_d = data['option_d']
        if 'correct_answer' in data:
            if data['correct_answer'] not in ['A', 'B', 'C', 'D']:
                return jsonify({'message': 'Correct answer must be A, B, C, or D'}), 400
            question.correct_answer = data['correct_answer']
        if 'points' in data:
            question.points = data['points']
        
        db.session.commit()
        
        return jsonify({'message': 'Question updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update question error: {str(e)}")
        return jsonify({'message': 'Failed to update question', 'error': str(e)}), 500

@app.route('/api/questions/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(question_id):
    try:
        question = Question.query.get(question_id)
        if not question:
            return jsonify({'message': 'Question not found'}), 404
            
        # Delete associated user answers first
        UserAnswer.query.filter_by(question_id=question_id).delete()
        
        db.session.delete(question)
        db.session.commit()
        
        return jsonify({'message': 'Question deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete question error: {str(e)}")
        return jsonify({'message': 'Failed to delete question', 'error': str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>', methods=['DELETE'])
@admin_required
def delete_quiz(quiz_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return jsonify({'message': 'Quiz not found'}), 404
            
        # Delete all associated data in the correct order
        # 1. Delete user answers for all questions in this quiz
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        for question in questions:
            UserAnswer.query.filter_by(question_id=question.id).delete()
        
        # 2. Delete all questions in this quiz
        Question.query.filter_by(quiz_id=quiz_id).delete()
        
        # 3. Delete all quiz attempts for this quiz
        QuizAttempt.query.filter_by(quiz_id=quiz_id).delete()
        
        # 4. Finally delete the quiz itself
        db.session.delete(quiz)
        db.session.commit()
        
        return jsonify({'message': 'Quiz deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete quiz error: {str(e)}")
        return jsonify({'message': 'Failed to delete quiz', 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent admin from deleting themselves
        if current_user_id == user_id:
            return jsonify({'message': 'Cannot delete your own account'}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Delete user's quiz attempts and answers
        user_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
        for attempt in user_attempts:
            UserAnswer.query.filter_by(attempt_id=attempt.id).delete()
            db.session.delete(attempt)
        
        # Delete user's created quizzes and their questions
        user_quizzes = Quiz.query.filter_by(created_by=user_id).all()
        for quiz in user_quizzes:
            # Delete questions and their answers
            questions = Question.query.filter_by(quiz_id=quiz.id).all()
            for question in questions:
                UserAnswer.query.filter_by(question_id=question.id).delete()
                db.session.delete(question)
            
            # Delete quiz attempts
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            db.session.delete(quiz)
        
        # Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete user error: {str(e)}")
        return jsonify({'message': 'Failed to delete user', 'error': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
            
        # Update user fields
        if 'username' in data:
            # Check if username already exists (excluding current user)
            existing_user = User.query.filter(
                and_(User.username == data['username'], User.id != user_id)
            ).first()
            if existing_user:
                return jsonify({'message': 'Username already exists'}), 400
            user.username = data['username']
            
        if 'email' in data:
            # Check if email already exists (excluding current user)
            existing_user = User.query.filter(
                and_(User.email == data['email'], User.id != user_id)
            ).first()
            if existing_user:
                return jsonify({'message': 'Email already exists'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({'message': 'User updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Update user error: {str(e)}")
        return jsonify({'message': 'Failed to update user', 'error': str(e)}), 500

@app.route('/api/admin/users', methods=['POST'])
@admin_required
def add_user():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        if not all([username, email, password]):
            return jsonify({'message': 'Username, email, and password are required'}), 400
        
        # Check if user exists
        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400
        
        # Validate role
        if role not in ['user', 'admin']:
            return jsonify({'message': 'Invalid role. Must be user or admin'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash.decode('utf-8'),
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Add user error: {str(e)}")
        return jsonify({'message': 'Failed to create user', 'error': str(e)}), 500
@app.route('/api/quizzes/<int:quiz_id>/start', methods=['POST'])
@jwt_required()
def start_quiz(quiz_id):
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get quiz details
        quiz = Quiz.query.filter_by(id=quiz_id, is_active=True).first()
        
        if not quiz:
            return jsonify({'message': 'Quiz not found or inactive'}), 404
        
        # Count questions
        question_count = Question.query.filter_by(quiz_id=quiz_id).count()
        
        # Create quiz attempt
        attempt = QuizAttempt(
            user_id=current_user_id,
            quiz_id=quiz_id,
            total_questions=question_count
        )
        
        db.session.add(attempt)
        db.session.commit()
        
        return jsonify({
            'attempt_id': attempt.id,
            'quiz_title': quiz.title,
            'time_limit': quiz.time_limit,
            'total_questions': question_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Start quiz error: {str(e)}")
        return jsonify({'message': 'Failed to start quiz', 'error': str(e)}), 500

@app.route('/api/attempts/<int:attempt_id>/submit', methods=['POST'])
@jwt_required()
def submit_quiz(attempt_id):
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400
            
        answers = data.get('answers', {})
        time_taken = data.get('time_taken', 0)
        
        # Verify attempt belongs to current user
        attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user_id).first()
        
        if not attempt:
            return jsonify({'message': 'Attempt not found or unauthorized'}), 404
        
        # Get all questions for this quiz
        questions = Question.query.filter_by(quiz_id=attempt.quiz_id).all()
        
        score = 0
        total_points = 0
        
        for question in questions:
            selected_answer = answers.get(str(question.id))
            is_correct = selected_answer == question.correct_answer
            
            if is_correct:
                score += question.points
            
            total_points += question.points
            
            # Save user answer
            user_answer = UserAnswer(
                attempt_id=attempt_id,
                question_id=question.id,
                selected_answer=selected_answer,
                is_correct=is_correct
            )
            db.session.add(user_answer)
        
        # Update quiz attempt
        attempt.score = score
        attempt.time_taken = time_taken
        attempt.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'score': score,
            'total_points': total_points,
            'percentage': (score / total_points * 100) if total_points > 0 else 0
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Submit quiz error: {str(e)}")
        return jsonify({'message': 'Failed to submit quiz', 'error': str(e)}), 500

# Admin routes
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.order_by(desc(User.created_at)).all()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            })
        
        return jsonify(user_list), 200
        
    except Exception as e:
        print(f"Get users error: {str(e)}")
        return jsonify({'message': 'Failed to get users', 'error': str(e)}), 422

@app.route('/api/admin/reports', methods=['GET'])
@admin_required
def get_reports():
    try:
        # Get all completed quiz attempts with explicit joins
        completed_attempts = db.session.query(
            QuizAttempt.id,
            QuizAttempt.user_id,
            QuizAttempt.quiz_id,
            QuizAttempt.score,
            QuizAttempt.total_questions,
            QuizAttempt.completed_at,
            Quiz.title.label('quiz_title'),
            User.username
        ).select_from(QuizAttempt).join(
            Quiz, QuizAttempt.quiz_id == Quiz.id
        ).join(
            User, QuizAttempt.user_id == User.id
        ).filter(
            QuizAttempt.completed_at.isnot(None)
        ).all()
        
        # Process quiz statistics
        quiz_stats_dict = {}
        user_stats_dict = {}
        daily_stats = {}
        score_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        for attempt in completed_attempts:
            # Calculate percentage safely
            if attempt.total_questions > 0:
                percentage = (attempt.score / attempt.total_questions) * 100
            else:
                percentage = 0
            
            # Quiz statistics
            quiz_title = attempt.quiz_title
            if quiz_title not in quiz_stats_dict:
                quiz_stats_dict[quiz_title] = {
                    'quiz_title': quiz_title,
                    'attempts': 0,
                    'total_percentage': 0,
                    'max_score': 0,
                    'min_score': 100
                }
            
            quiz_stats_dict[quiz_title]['attempts'] += 1
            quiz_stats_dict[quiz_title]['total_percentage'] += percentage
            quiz_stats_dict[quiz_title]['max_score'] = max(quiz_stats_dict[quiz_title]['max_score'], percentage)
            quiz_stats_dict[quiz_title]['min_score'] = min(quiz_stats_dict[quiz_title]['min_score'], percentage)
            
            # User statistics
            username = attempt.username
            if username not in user_stats_dict:
                user_stats_dict[username] = {
                    'username': username,
                    'attempts': 0,
                    'total_percentage': 0,
                    'best_score': 0
                }
            
            user_stats_dict[username]['attempts'] += 1
            user_stats_dict[username]['total_percentage'] += percentage
            user_stats_dict[username]['best_score'] = max(user_stats_dict[username]['best_score'], percentage)
            
            # Daily activity (last 7 days)
            if attempt.completed_at >= datetime.utcnow() - timedelta(days=7):
                date_str = attempt.completed_at.date().isoformat()
                if date_str not in daily_stats:
                    daily_stats[date_str] = {'total_percentage': 0, 'count': 0}
                daily_stats[date_str]['total_percentage'] += percentage
                daily_stats[date_str]['count'] += 1
            
            # Score distribution
            if percentage >= 80:
                score_counts['excellent'] += 1
            elif percentage >= 60:
                score_counts['good'] += 1
            elif percentage >= 40:
                score_counts['fair'] += 1
            else:
                score_counts['poor'] += 1
        
        # Calculate averages for quiz stats
        quiz_statistics = []
        for stats in quiz_stats_dict.values():
            avg_score = stats['total_percentage'] / stats['attempts'] if stats['attempts'] > 0 else 0
            min_score = stats['min_score'] if stats['attempts'] > 0 else 0
            quiz_statistics.append({
                'quiz_title': stats['quiz_title'],
                'attempts': stats['attempts'],
                'avg_score': round(avg_score, 2),
                'max_score': round(stats['max_score'], 2),
                'min_score': round(min_score, 2)
            })
        
        # Calculate averages for user stats
        user_performance = []
        for stats in user_stats_dict.values():
            avg_score = stats['total_percentage'] / stats['attempts'] if stats['attempts'] > 0 else 0
            user_performance.append({
                'username': stats['username'],
                'attempts': stats['attempts'],
                'avg_score': round(avg_score, 2),
                'best_score': round(stats['best_score'], 2)
            })
        
        # Calculate daily averages
        user_activity = []
        for date_str, stats in daily_stats.items():
            avg_percentage = stats['total_percentage'] / stats['count'] if stats['count'] > 0 else 0
            user_activity.append({
                'date': date_str,
                'avg_percentage': round(avg_percentage, 2)
            })
        
        # Sort results
        quiz_statistics.sort(key=lambda x: x['attempts'], reverse=True)
        user_performance.sort(key=lambda x: x['avg_score'], reverse=True)
        user_activity.sort(key=lambda x: x['date'])
        
        return jsonify({
            'quiz_statistics': quiz_statistics,
            'user_performance': user_performance,
            'user_activity': user_activity,
            'score_distribution': score_counts
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Get reports error: {str(e)}")
        return jsonify({'message': 'Failed to get reports', 'error': str(e)}), 422

@app.route('/api/user/attempts', methods=['GET'])
@jwt_required()
def get_user_attempts():
    try:
        current_user_id = int(get_jwt_identity())
        
        attempts = db.session.query(
            QuizAttempt.id,
            Quiz.title,
            QuizAttempt.score,
            QuizAttempt.total_questions,
            QuizAttempt.time_taken,
            QuizAttempt.started_at,
            QuizAttempt.completed_at,
            func.coalesce(
                (func.cast(QuizAttempt.score, db.Float) / 
                 func.nullif(QuizAttempt.total_questions, 0) * 100), 0
            ).label('percentage')
        ).join(Quiz).filter(
            and_(
                QuizAttempt.user_id == current_user_id,
                QuizAttempt.completed_at.isnot(None)
            )
        ).order_by(desc(QuizAttempt.completed_at)).all()
        
        attempt_list = []
        for attempt in attempts:
            attempt_list.append({
                'id': attempt.id,
                'quiz_title': attempt.title,
                'score': attempt.score,
                'total_questions': attempt.total_questions,
                'time_taken': attempt.time_taken,
                'started_at': attempt.started_at.isoformat(),
                'completed_at': attempt.completed_at.isoformat(),
                'percentage': round(attempt.percentage, 2) if attempt.percentage else 0
            })
        
        return jsonify(attempt_list), 200
        
    except Exception as e:
        print(f"Get user attempts error: {str(e)}")
        return jsonify({'message': 'Failed to get user attempts', 'error': str(e)}), 422

@app.route('/api/quizzes/<int:quiz_id>/attempts', methods=['GET'])
@jwt_required()
def get_quiz_attempts(quiz_id):
    try:
        # Check if user is admin or if it's their own quiz attempts
        current_user_id = int(get_jwt_identity())
        current_user = User.query.get(current_user_id)
        
        if current_user.role == 'admin':
            # Admin can see all attempts for any quiz
            attempts = db.session.query(
                QuizAttempt.id,
                QuizAttempt.score,
                QuizAttempt.total_questions,
                QuizAttempt.time_taken,
                QuizAttempt.completed_at,
                User.username,
                func.coalesce(
                    (func.cast(QuizAttempt.score, db.Float) / 
                     func.nullif(QuizAttempt.total_questions, 0) * 100), 0
                ).label('percentage')
            ).join(User).filter(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.completed_at.isnot(None)
                )
            ).order_by(desc(QuizAttempt.completed_at)).all()
        else:
            # Regular users can only see their own attempts
            attempts = db.session.query(
                QuizAttempt.id,
                QuizAttempt.score,
                QuizAttempt.total_questions,
                QuizAttempt.time_taken,
                QuizAttempt.completed_at,
                User.username,
                func.coalesce(
                    (func.cast(QuizAttempt.score, db.Float) / 
                     func.nullif(QuizAttempt.total_questions, 0) * 100), 0
                ).label('percentage')
            ).join(User).filter(
                and_(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.user_id == current_user_id,
                    QuizAttempt.completed_at.isnot(None)
                )
            ).order_by(desc(QuizAttempt.completed_at)).all()
        
        attempt_list = []
        for attempt in attempts:
            attempt_list.append({
                'id': attempt.id,
                'username': attempt.username,
                'score': attempt.score,
                'total_questions': attempt.total_questions,
                'time_taken': attempt.time_taken,
                'completed_at': attempt.completed_at.isoformat(),
                'percentage': round(attempt.percentage, 2) if attempt.percentage else 0
            })
        
        return jsonify(attempt_list), 200
        
    except Exception as e:
        print(f"Get quiz attempts error: {str(e)}")
        return jsonify({'message': 'Failed to get quiz attempts', 'error': str(e)}), 422

# Job management routes (Admin only)
@app.route('/api/admin/jobs/test-reminders', methods=['POST'])
@admin_required
def test_reminders():
    try:
        count = test_user_reminders()
        return jsonify({
            'message': f'Successfully sent {count} reminder emails',
            'count': count
        }), 200
    except Exception as e:
        print(f"Test reminders error: {str(e)}")
        return jsonify({'message': 'Failed to send reminders', 'error': str(e)}), 500

@app.route('/api/admin/jobs/test-admin-report', methods=['POST'])
@admin_required
def test_admin_report():
    try:
        count = test_admin_report()
        return jsonify({
            'message': f'Successfully sent {count} admin report emails',
            'count': count
        }), 200
    except Exception as e:
        print(f"Test admin report error: {str(e)}")
        return jsonify({'message': 'Failed to send admin report', 'error': str(e)}), 500

@app.route('/api/admin/jobs/test-cleanup', methods=['POST'])
@admin_required
def test_cleanup():
    try:
        success = test_weekly_cleanup()
        return jsonify({
            'message': 'Weekly cleanup completed successfully' if success else 'Weekly cleanup failed',
            'success': success
        }), 200
    except Exception as e:
        print(f"Test cleanup error: {str(e)}")
        return jsonify({'message': 'Failed to run cleanup', 'error': str(e)}), 500

@app.route('/api/admin/jobs/inactive-users', methods=['GET'])
@admin_required
def get_inactive_users():
    try:
        users = test_get_inactive_users()
        return jsonify({
            'message': f'Found {len(users)} inactive users',
            'users': users
        }), 200
    except Exception as e:
        print(f"Get inactive users error: {str(e)}")
        return jsonify({'message': 'Failed to get inactive users', 'error': str(e)}), 500

@app.route('/api/admin/jobs/daily-stats', methods=['GET'])
@admin_required
def get_daily_stats():
    try:
        stats = test_get_daily_stats()
        return jsonify({
            'message': 'Daily statistics retrieved successfully',
            'stats': stats
        }), 200
    except Exception as e:
        print(f"Get daily stats error: {str(e)}")
        return jsonify({'message': 'Failed to get daily stats', 'error': str(e)}), 500

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    
    # Start the job scheduler
    print("Starting job scheduler...")
    job_scheduler.start()
    
    try:
        print("Starting Flask server on http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Stop the job scheduler when the app shuts down
        job_scheduler.stop()