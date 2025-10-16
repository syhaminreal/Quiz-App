#!/usr/bin/env python3
"""
Database Migration Script
Migrates existing quiz_app.db to new schema with subjects and chapters
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    db_path = 'instance/quiz_app.db'
    
    if not os.path.exists(db_path):
        print("No existing database found. Will create new one.")
        return
    
    print("Starting database migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        subjects_exists = cursor.fetchone() is not None
        
        # Check if chapters table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chapters'")
        chapters_exists = cursor.fetchone() is not None
        
        # Check if quizzes table has chapter_id column
        cursor.execute("PRAGMA table_info(quizzes)")
        columns = [column[1] for column in cursor.fetchall()]
        has_chapter_id = 'chapter_id' in columns
        
        print(f"Subjects table exists: {subjects_exists}")
        print(f"Chapters table exists: {chapters_exists}")
        print(f"Quizzes has chapter_id: {has_chapter_id}")
        
        # Create subjects table if it doesn't exist
        if not subjects_exists:
            print("Creating subjects table...")
            cursor.execute('''
                CREATE TABLE subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Insert default subject
            cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            admin_id = admin_user[0] if admin_user else 1
            
            cursor.execute('''
                INSERT INTO subjects (name, description, created_by)
                VALUES ('General Knowledge', 'Default subject for existing quizzes', ?)
            ''', (admin_id,))
            
            print("Created subjects table with default subject")
        
        # Create chapters table if it doesn't exist
        if not chapters_exists:
            print("Creating chapters table...")
            cursor.execute('''
                CREATE TABLE chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    subject_id INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Insert default chapter
            cursor.execute("SELECT id FROM subjects LIMIT 1")
            subject_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
            admin_user = cursor.fetchone()
            admin_id = admin_user[0] if admin_user else 1
            
            cursor.execute('''
                INSERT INTO chapters (name, description, subject_id, created_by)
                VALUES ('General', 'Default chapter for existing quizzes', ?, ?)
            ''', (subject_id, admin_id))
            
            print("Created chapters table with default chapter")
        
        # Add chapter_id to quizzes table if it doesn't exist
        if not has_chapter_id:
            print("Adding chapter_id to quizzes table...")
            
            # Get the default chapter ID
            cursor.execute("SELECT id FROM chapters LIMIT 1")
            chapter_result = cursor.fetchone()
            
            if not chapter_result:
                # Create default chapter if none exists
                cursor.execute("SELECT id FROM subjects LIMIT 1")
                subject_result = cursor.fetchone()
                
                if not subject_result:
                    # Create default subject if none exists
                    cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
                    admin_user = cursor.fetchone()
                    admin_id = admin_user[0] if admin_user else 1
                    
                    cursor.execute('''
                        INSERT INTO subjects (name, description, created_by)
                        VALUES ('General Knowledge', 'Default subject for existing quizzes', ?)
                    ''', (admin_id,))
                    subject_id = cursor.lastrowid
                else:
                    subject_id = subject_result[0]
                
                cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
                admin_user = cursor.fetchone()
                admin_id = admin_user[0] if admin_user else 1
                
                cursor.execute('''
                    INSERT INTO chapters (name, description, subject_id, created_by)
                    VALUES ('General', 'Default chapter for existing quizzes', ?, ?)
                ''', (subject_id, admin_id))
                chapter_id = cursor.lastrowid
            else:
                chapter_id = chapter_result[0]
            
            # Create new quizzes table with chapter_id
            cursor.execute('''
                CREATE TABLE quizzes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    chapter_id INTEGER NOT NULL,
                    time_limit INTEGER DEFAULT 30,
                    is_active BOOLEAN DEFAULT 1,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chapter_id) REFERENCES chapters (id),
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            ''')
            
            # Copy data from old table to new table
            cursor.execute(f'''
                INSERT INTO quizzes_new (id, title, description, chapter_id, time_limit, is_active, created_by, created_at)
                SELECT id, title, description, {chapter_id}, time_limit, is_active, created_by, created_at
                FROM quizzes
            ''')
            
            # Drop old table and rename new table
            cursor.execute('DROP TABLE quizzes')
            cursor.execute('ALTER TABLE quizzes_new RENAME TO quizzes')
            
            print(f"Updated quizzes table with chapter_id (default: {chapter_id})")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()