import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    def __init__(self, app=None):
        if app:
            self.init_app(app)
            
    def init_app(self, app):
        self.host = app.config.get('MAIL_SERVER')
        self.port = app.config.get('MAIL_PORT')
        self.username = app.config.get('MAIL_USERNAME')
        self.password = app.config.get('MAIL_PASSWORD')
        self.use_tls = app.config.get('MAIL_USE_TLS', False)
        self.use_ssl = app.config.get('MAIL_USE_SSL', False)
        self.sender = app.config.get('MAIL_DEFAULT_SENDER')
        
    def send_email(self, to, subject, template):
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender
            msg['To'] = to
            
            msg.attach(MIMEText(template, 'html'))
            
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
                
            server.sendmail(self.sender, to, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
            
    def send_verification_email(self, user, verification_url):
        subject = "Verify Your Email Address - ESGenerator"
        template = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to ESGenerator</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user.username},</p>
                        <p>Thank you for registering with ESGenerator. To complete your registration, please verify your email address by clicking the button below:</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </p>
                        <p>If the button doesn't work, please copy and paste the following link into your browser:</p>
                        <p>{verification_url}</p>
                        <p>This link will expire in 24 hours.</p>
                        <p>Best regards,<br>The ESGenerator Team</p>
                    </div>
                    <div class="footer">
                        <p>If you did not create an account, please ignore this email.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(user.email, subject, template)
        
    def send_password_reset_email(self, user, reset_url):
        subject = "Reset Your Password - ESGenerator"
        template = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #2196F3; color: white; padding: 10px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .button {{ background-color: #2196F3; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>ESGenerator Password Reset</h1>
                    </div>
                    <div class="content">
                        <p>Hello {user.username},</p>
                        <p>We received a request to reset your password. If you made this request, please click the button below to reset your password:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>If the button doesn't work, please copy and paste the following link into your browser:</p>
                        <p>{reset_url}</p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p>
                        <p>Best regards,<br>The ESGenerator Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message, please do not reply.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(user.email, subject, template)