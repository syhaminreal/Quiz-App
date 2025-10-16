# Data Structures and Algorithms Implementation

## 1. Hashing Algorithm (Password Security)

### Bcrypt Hashing Algorithm with Salt Generation

```python
# Implementation in backend/app.py (lines 210, 906)
import bcrypt

def hash_password(password):
    """
    Uses bcrypt hashing algorithm with salt generation
    Time Complexity: O(2^cost) where cost is the work factor
    Space Complexity: O(1)
    """
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password, stored_hash):
    """
    Verifies password against stored hash
    Time Complexity: O(2^cost)
    Space Complexity: O(1)
    """
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

# Usage in registration
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Usage in login
if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
    # Authentication successful
```

## 2. Sorting Algorithm (Quiz Statistics)

### Timsort (Hybrid Merge Sort + Insertion Sort)

```python
# Implementation in backend/app.py (lines 1161-1162)

def sort_quiz_statistics(quiz_statistics):
    """
    Sorts quiz statistics by number of attempts in descending order
    Uses Python's Timsort algorithm (hybrid of merge sort and insertion sort)
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    quiz_statistics.sort(key=lambda x: x['attempts'], reverse=True)
    return quiz_statistics

def sort_user_performance(user_performance):
    """
    Sorts user performance by average score in descending order
    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """
    user_performance.sort(key=lambda x: x['avg_score'], reverse=True)
    return user_performance

# Usage in analytics endpoint
quiz_statistics.sort(key=lambda x: x['attempts'], reverse=True)
user_performance.sort(key=lambda x: x['avg_score'], reverse=True)
```

## 3. Filtering Algorithm (User Search)

### Linear Search with Multiple Predicates

```python
# Implementation in backend/app.py (lines 201-204, 851-854)

def filter_existing_user(username, email, exclude_id=None):
    """
    Linear search through user records with multiple conditions
    Time Complexity: O(n) where n is number of users
    Space Complexity: O(1)
    """
    users = User.query.all()

    for user in users:
        if exclude_id and user.id == exclude_id:
            continue
        if user.username == username or user.email == email:
            return user

    return None

# Optimized database version used in code
existing_user = User.query.filter(
    or_(User.username == username, User.email == email)
).first()
```

## 4. Aggregation Algorithm (Statistics Calculation)

### Single-Pass Aggregation with Hash Set

```python
# Implementation in backend/jobs.py (lines 100-150)

def calculate_daily_statistics(quiz_attempts):
    """
    Aggregates quiz attempt data to compute statistics
    Time Complexity: O(n) where n is number of attempts
    Space Complexity: O(1)
    """
    if not quiz_attempts:
        return {
            'active_users': 0,
            'total_attempts': 0,
            'avg_score': 0,
            'quizzes_taken': 0
        }

    unique_users = set()
    unique_quizzes = set()
    total_score = 0

    for attempt in quiz_attempts:
        unique_users.add(attempt.user_id)
        unique_quizzes.add(attempt.quiz_id)
        percentage = (attempt.score / attempt.total_questions) * 100
        total_score += percentage

    return {
        'active_users': len(unique_users),
        'total_attempts': len(quiz_attempts),
        'avg_score': round(total_score / len(quiz_attempts), 2),
        'quizzes_taken': len(unique_quizzes)
    }
```

## 5. Cascade Delete Algorithm (Data Cleanup)

### Depth-First Traversal (DFS) for Hierarchical Deletion

```python
# Implementation in backend/app.py (lines 285-310, 395-415)

def cascade_delete_subject(subject_id):
    """
    Recursively deletes subject and all related data
    Uses depth-first traversal approach
    Time Complexity: O(n) where n is total related records
    Space Complexity: O(d) where d is depth of relationships
    """
    subject = Subject.query.get(subject_id)

    # Level 1: Get all chapters
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()

    for chapter in chapters:
        # Level 2: Get all quizzes
        quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()

        for quiz in quizzes:
            # Level 3: Get all questions
            questions = Question.query.filter_by(quiz_id=quiz.id).all()

            for question in questions:
                # Level 4: Delete user answers
                UserAnswer.query.filter_by(question_id=question.id).delete()

            # Delete questions
            Question.query.filter_by(quiz_id=quiz.id).delete()

            # Delete quiz attempts
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()

            # Delete quiz
            db.session.delete(quiz)

        # Delete chapter
        db.session.delete(chapter)

    # Delete subject
    db.session.delete(subject)
    db.session.commit()
```
