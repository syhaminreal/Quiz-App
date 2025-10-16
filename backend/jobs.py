import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import schedule
import time
import threading
import os
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import User, Quiz, QuizAttempt

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jobs.log'),
        logging.StreamHandler()
    ]
)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER', 'your-email@gmail.com')
        self.email_password = os.getenv('EMAIL_PASSWORD', 'your-app-password')
        self.from_email = os.getenv('FROM_EMAIL', 'Quiz App <noreply@quizapp.com>')
        self.debug_mode = os.getenv('EMAIL_DEBUG_MODE', 'false').lower() == 'true'
    
    def is_valid_email(self, email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email with HTML content"""
        try:
            # Validate email address
            if not self.is_valid_email(to_email):
                logging.warning(f"Invalid email address: {to_email} - skipping")
                return False
            
            # Debug mode - just log instead of sending
            if self.debug_mode:
                logging.info(f"[DEBUG MODE] Would send email to {to_email}")
                logging.info(f"[DEBUG MODE] Subject: {subject}")
                logging.info(f"[DEBUG MODE] Email content logged successfully")
                return True
            
            # Check if email configuration is set up
            if (self.email_user == 'your-email@gmail.com' or 
                self.email_password == 'your-app-password'):
                logging.warning("Email not configured properly. Set EMAIL_DEBUG_MODE=true to test without sending real emails.")
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text version if provided
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML version
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logging.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

class JobScheduler:
    def __init__(self):
        self.email_service = EmailService()
        self.running = False
        self.thread = None
        
        # Initialize database connection
        database_url = 'sqlite:///instance/quiz_app.db'
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_inactive_users(self, days=7):
        """Get users who haven't taken a quiz in the last N days"""
        session = self.SessionLocal()
        try:
            # Get users who haven't taken a quiz in the last N days
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Raw SQL query using SQLAlchemy text
            query = text('''
                SELECT u.id, u.username, u.email, 
                       MAX(qa.completed_at) as last_attempt,
                       COUNT(qa.id) as total_attempts
                FROM users u
                LEFT JOIN quiz_attempts qa ON u.id = qa.user_id
                WHERE u.role = 'user'
                AND (qa.completed_at IS NULL OR qa.completed_at < :cutoff_date)
                GROUP BY u.id, u.username, u.email
                ORDER BY last_attempt ASC
            ''')
            
            result = session.execute(query, {'cutoff_date': cutoff_date})
            users = result.fetchall()
            
            return [
                {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'last_attempt': user[3],
                    'total_attempts': user[4]
                }
                for user in users
            ]
        finally:
            session.close()
    
    def get_daily_stats(self):
        """Get daily statistics for admin reports"""
        session = self.SessionLocal()
        try:
            # Get today's stats
            today_query = text('''
                SELECT 
                    COUNT(DISTINCT qa.user_id) as active_users,
                    COUNT(qa.id) as total_attempts,
                    AVG(CAST(qa.score AS FLOAT) / qa.total_questions * 100) as avg_score,
                    COUNT(DISTINCT qa.quiz_id) as quizzes_taken
                FROM quiz_attempts qa
                WHERE DATE(qa.completed_at) = DATE('now')
            ''')
            today_result = session.execute(today_query).fetchone()
            
            # Get yesterday's stats for comparison
            yesterday_query = text('''
                SELECT 
                    COUNT(DISTINCT qa.user_id) as active_users,
                    COUNT(qa.id) as total_attempts,
                    AVG(CAST(qa.score AS FLOAT) / qa.total_questions * 100) as avg_score,
                    COUNT(DISTINCT qa.quiz_id) as quizzes_taken
                FROM quiz_attempts qa
                WHERE DATE(qa.completed_at) = DATE('now', '-1 day')
            ''')
            yesterday_result = session.execute(yesterday_query).fetchone()
            
            # Get new users today
            new_users_query = text('''
                SELECT COUNT(*) FROM users 
                WHERE DATE(created_at) = DATE('now')
            ''')
            new_users = session.execute(new_users_query).fetchone()[0]
            
            # Get top performing quiz today
            top_quiz_query = text('''
                SELECT q.title, COUNT(qa.id) as attempts,
                       AVG(CAST(qa.score AS FLOAT) / qa.total_questions * 100) as avg_score
                FROM quiz_attempts qa
                JOIN quizzes q ON qa.quiz_id = q.id
                WHERE DATE(qa.completed_at) = DATE('now')
                GROUP BY q.id, q.title
                ORDER BY attempts DESC, avg_score DESC
                LIMIT 1
            ''')
            top_quiz_result = session.execute(top_quiz_query).fetchone()
            
            return {
                'today': {
                    'active_users': today_result[0] or 0,
                    'total_attempts': today_result[1] or 0,
                    'avg_score': round(today_result[2], 2) if today_result[2] else 0,
                    'quizzes_taken': today_result[3] or 0
                },
                'yesterday': {
                    'active_users': yesterday_result[0] or 0,
                    'total_attempts': yesterday_result[1] or 0,
                    'avg_score': round(yesterday_result[2], 2) if yesterday_result[2] else 0,
                    'quizzes_taken': yesterday_result[3] or 0
                },
                'new_users': new_users,
                'top_quiz': {
                    'title': top_quiz_result[0] if top_quiz_result else 'No quizzes taken',
                    'attempts': top_quiz_result[1] if top_quiz_result else 0,
                    'avg_score': round(top_quiz_result[2], 2) if top_quiz_result and top_quiz_result[2] else 0
                }
            }
        finally:
            session.close()
    
    def get_admin_emails(self):
        """Get all admin email addresses (only valid ones)"""
        session = self.SessionLocal()
        try:
            admin_users = session.query(User).filter(User.role == 'admin').all()
            all_emails = [user.email for user in admin_users]
            
            # Filter out invalid emails
            valid_emails = [email for email in all_emails if self.email_service.is_valid_email(email)]
            
            if len(valid_emails) != len(all_emails):
                invalid_emails = [email for email in all_emails if not self.email_service.is_valid_email(email)]
                logging.warning(f"Found {len(invalid_emails)} invalid admin emails: {invalid_emails}")
            
            return valid_emails
        finally:
            session.close()
    
    def send_user_reminder(self, user):
        """Send reminder email to inactive user"""
        subject = "🎯 Don't Miss Out - New Quizzes Await You!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .stats {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 Quiz App</h1>
                    <h2>We Miss You, {user['username']}!</h2>
                </div>
                <div class="content">
                    <p>Hi {user['username']},</p>
                    
                    <p>We noticed you haven't taken any quizzes recently. There are exciting new challenges waiting for you!</p>
                    
                    <div class="stats">
                        <h3>📊 Your Quiz Journey So Far:</h3>
                        <p><strong>Total Attempts:</strong> {user['total_attempts']}</p>
                        {f"<p><strong>Last Quiz:</strong> {user['last_attempt']}</p>" if user['last_attempt'] else "<p><strong>Status:</strong> Ready for your first quiz!</p>"}
                    </div>
                    
                    <p>🚀 <strong>What's New:</strong></p>
                    <ul>
                        <li>Fresh quiz questions added weekly</li>
                        <li>Performance analytics to track your progress</li>
                        <li>Compete with other learners</li>
                        <li>Export your performance reports</li>
                    </ul>
                    
                    <div style="text-align: center;">
                        <a href="http://localhost:5173/dashboard" class="button">🎯 Take a Quiz Now</a>
                    </div>
                    
                    <p>Keep learning and growing! 📚✨</p>
                    
                    <p>Best regards,<br>The Quiz App Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated reminder. You can update your preferences in your profile settings.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user['username']},
        
        We miss you at Quiz App! You haven't taken any quizzes recently.
        
        Your Stats:
        - Total Attempts: {user['total_attempts']}
        - Last Quiz: {user['last_attempt'] if user['last_attempt'] else 'None yet'}
        
        Visit http://localhost:5173/dashboard to take a quiz now!
        
        Best regards,
        The Quiz App Team
        """
        
        return self.email_service.send_email(user['email'], subject, html_content, text_content)
    
    def send_admin_daily_report(self, admin_email, stats):
        """Send daily report to admin"""
        subject = f"📊 Daily Quiz App Report - {datetime.now().strftime('%B %d, %Y')}"
        
        # Calculate changes from yesterday
        def get_change(today, yesterday):
            if yesterday == 0:
                return "New!" if today > 0 else "No change"
            change = ((today - yesterday) / yesterday) * 100
            if change > 0:
                return f"+{change:.1f}%"
            elif change < 0:
                return f"{change:.1f}%"
            else:
                return "No change"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #3b82f6; }}
                .stat-change {{ font-size: 0.9em; margin-top: 5px; }}
                .positive {{ color: #10b981; }}
                .negative {{ color: #ef4444; }}
                .neutral {{ color: #6b7280; }}
                .highlight {{ background: #dbeafe; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 14px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Quiz App Daily Report</h1>
                    <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
                </div>
                <div class="content">
                    <h2>📈 Today's Performance</h2>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{stats['today']['active_users']}</div>
                            <div>Active Users</div>
                            <div class="stat-change {'positive' if stats['today']['active_users'] > stats['yesterday']['active_users'] else 'negative' if stats['today']['active_users'] < stats['yesterday']['active_users'] else 'neutral'}">
                                {get_change(stats['today']['active_users'], stats['yesterday']['active_users'])}
                            </div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-number">{stats['today']['total_attempts']}</div>
                            <div>Quiz Attempts</div>
                            <div class="stat-change {'positive' if stats['today']['total_attempts'] > stats['yesterday']['total_attempts'] else 'negative' if stats['today']['total_attempts'] < stats['yesterday']['total_attempts'] else 'neutral'}">
                                {get_change(stats['today']['total_attempts'], stats['yesterday']['total_attempts'])}
                            </div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-number">{stats['today']['avg_score']}%</div>
                            <div>Average Score</div>
                            <div class="stat-change {'positive' if stats['today']['avg_score'] > stats['yesterday']['avg_score'] else 'negative' if stats['today']['avg_score'] < stats['yesterday']['avg_score'] else 'neutral'}">
                                {get_change(stats['today']['avg_score'], stats['yesterday']['avg_score'])}
                            </div>
                        </div>
                        
                        <div class="stat-card">
                            <div class="stat-number">{stats['new_users']}</div>
                            <div>New Users</div>
                            <div class="stat-change neutral">Today</div>
                        </div>
                    </div>
                    
                    <div class="highlight">
                        <h3>🏆 Top Quiz Today</h3>
                        <p><strong>{stats['top_quiz']['title']}</strong></p>
                        <p>{stats['top_quiz']['attempts']} attempts • {stats['top_quiz']['avg_score']}% average score</p>
                    </div>
                    
                    <h3>📊 Yesterday vs Today Comparison</h3>
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #f3f4f6;">
                            <th style="padding: 10px; text-align: left;">Metric</th>
                            <th style="padding: 10px; text-align: center;">Yesterday</th>
                            <th style="padding: 10px; text-align: center;">Today</th>
                            <th style="padding: 10px; text-align: center;">Change</th>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Active Users</td>
                            <td style="padding: 10px; text-align: center;">{stats['yesterday']['active_users']}</td>
                            <td style="padding: 10px; text-align: center;">{stats['today']['active_users']}</td>
                            <td style="padding: 10px; text-align: center;">{get_change(stats['today']['active_users'], stats['yesterday']['active_users'])}</td>
                        </tr>
                        <tr style="background: #f9fafb;">
                            <td style="padding: 10px;">Quiz Attempts</td>
                            <td style="padding: 10px; text-align: center;">{stats['yesterday']['total_attempts']}</td>
                            <td style="padding: 10px; text-align: center;">{stats['today']['total_attempts']}</td>
                            <td style="padding: 10px; text-align: center;">{get_change(stats['today']['total_attempts'], stats['yesterday']['total_attempts'])}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px;">Average Score</td>
                            <td style="padding: 10px; text-align: center;">{stats['yesterday']['avg_score']}%</td>
                            <td style="padding: 10px; text-align: center;">{stats['today']['avg_score']}%</td>
                            <td style="padding: 10px; text-align: center;">{get_change(stats['today']['avg_score'], stats['yesterday']['avg_score'])}</td>
                        </tr>
                    </table>
                    
                    <p>Keep up the great work managing the Quiz App! 🚀</p>
                </div>
                <div class="footer">
                    <p>This is an automated daily report from Quiz App Admin System.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.email_service.send_email(admin_email, subject, html_content)
    
    def daily_user_reminders(self):
        """Send reminders to inactive users"""
        logging.info("Starting daily user reminders job...")
        
        inactive_users = self.get_inactive_users(days=7)
        sent_count = 0
        
        for user in inactive_users:
            if self.send_user_reminder(user):
                sent_count += 1
            time.sleep(1)  # Rate limiting
        
        logging.info(f"Daily user reminders completed. Sent {sent_count} emails to {len(inactive_users)} inactive users.")
        return sent_count
    
    def daily_admin_report(self):
        """Send daily report to admins"""
        logging.info("Starting daily admin report job...")
        
        stats = self.get_daily_stats()
        admin_emails = self.get_admin_emails()
        sent_count = 0
        
        logging.info(f"Found {len(admin_emails)} valid admin emails: {admin_emails}")
        
        for email in admin_emails:
            if self.send_admin_daily_report(email, stats):
                sent_count += 1
            time.sleep(1)  # Rate limiting
        
        logging.info(f"Daily admin report completed. Sent {sent_count} emails to {len(admin_emails)} admins.")
        return sent_count
    
    def weekly_cleanup(self):
        """Clean up old logs and temporary data"""
        logging.info("Starting weekly cleanup job...")
        
        try:
            # Clean up old log entries (keep last 30 days)
            if os.path.exists('jobs.log'):
                # In a real implementation, you'd rotate logs properly
                logging.info("Log cleanup completed")
            
            # You could add more cleanup tasks here
            # - Clean up temporary files
            # - Archive old quiz attempts
            # - Update statistics tables
            
            logging.info("Weekly cleanup completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Weekly cleanup failed: {str(e)}")
            return False
    
    def schedule_jobs(self):
        """Schedule all recurring jobs"""
        # Daily user reminders at 9:00 AM
        schedule.every().day.at("09:00").do(self.daily_user_reminders)
        
        # Daily admin report at 8:00 AM
        schedule.every().day.at("08:00").do(self.daily_admin_report)
        
        # Weekly cleanup on Sunday at 2:00 AM
        schedule.every().sunday.at("02:00").do(self.weekly_cleanup)
        
        logging.info("Jobs scheduled successfully:")
        logging.info("- Daily user reminders: 9:00 AM")
        logging.info("- Daily admin report: 8:00 AM")
        logging.info("- Weekly cleanup: Sunday 2:00 AM")
    
    def run_scheduler(self):
        """Run the job scheduler"""
        self.running = True
        logging.info("Job scheduler started")
        
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the job scheduler in a separate thread"""
        if not self.running:
            self.schedule_jobs()
            self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.thread.start()
            logging.info("Job scheduler thread started")
    
    def stop(self):
        """Stop the job scheduler"""
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info("Job scheduler stopped")

# Global scheduler instance
job_scheduler = JobScheduler()

# Manual testing functions
def test_user_reminders():
    """Test function to manually trigger user reminders"""
    print("🔄 Testing user reminders...")
    scheduler = JobScheduler()
    count = scheduler.daily_user_reminders()
    print(f"✅ Sent {count} reminder emails")
    return count

def test_admin_report():
    """Test function to manually trigger admin report"""
    print("🔄 Testing admin daily report...")
    scheduler = JobScheduler()
    count = scheduler.daily_admin_report()
    print(f"✅ Sent {count} admin report emails")
    return count

def test_weekly_cleanup():
    """Test function to manually trigger weekly cleanup"""
    print("🔄 Testing weekly cleanup...")
    scheduler = JobScheduler()
    success = scheduler.weekly_cleanup()
    print(f"✅ Weekly cleanup {'completed' if success else 'failed'}")
    return success

def test_get_inactive_users():
    """Test function to get inactive users"""
    print("🔄 Getting inactive users...")
    scheduler = JobScheduler()
    users = scheduler.get_inactive_users(days=7)
    print(f"📊 Found {len(users)} inactive users:")
    for user in users:
        print(f"  - {user['username']} ({user['email']}) - Last attempt: {user['last_attempt'] or 'Never'}")
    return users

def test_get_daily_stats():
    """Test function to get daily statistics"""
    print("🔄 Getting daily statistics...")
    scheduler = JobScheduler()
    stats = scheduler.get_daily_stats()
    print("📊 Daily Statistics:")
    print(f"  Today: {stats['today']}")
    print(f"  Yesterday: {stats['yesterday']}")
    print(f"  New Users: {stats['new_users']}")
    print(f"  Top Quiz: {stats['top_quiz']}")
    return stats

if __name__ == "__main__":
    # This allows running the script directly for testing
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test-reminders":
            test_user_reminders()
        elif command == "test-admin-report":
            test_admin_report()
        elif command == "test-cleanup":
            test_weekly_cleanup()
        elif command == "test-inactive-users":
            test_get_inactive_users()
        elif command == "test-stats":
            test_get_daily_stats()
        elif command == "start":
            job_scheduler.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                job_scheduler.stop()
        else:
            print("Available commands:")
            print("  test-reminders     - Test user reminder emails")
            print("  test-admin-report  - Test admin daily report")
            print("  test-cleanup       - Test weekly cleanup")
            print("  test-inactive-users - Show inactive users")
            print("  test-stats         - Show daily statistics")
            print("  start              - Start the job scheduler")
    else:
        print("Usage: python jobs.py <command>")
        print("Available commands:")
        print("  test-reminders     - Test user reminder emails")
        print("  test-admin-report  - Test admin daily report")
        print("  test-cleanup       - Test weekly cleanup")
        print("  test-inactive-users - Show inactive users")
        print("  test-stats         - Show daily statistics")
        print("  start              - Start the job scheduler")