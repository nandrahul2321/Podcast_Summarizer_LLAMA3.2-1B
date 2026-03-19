from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import asyncio
import secrets
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()  # Load SMTP and other secrets from .env

from db import users_collection, password_resets_collection
from home import home_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or 'dev-secret-key'


# -------------------- Async Safe Runner --------------------
def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)
# ----------------------------------------------------------


# -------------------- Flask-Login Setup --------------------
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.session_protection = "strong"
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password_hash = user_data['password']


@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = users_collection.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None
    except Exception:
        return None


# -------------------- Routes --------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not email or '@' not in email:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('signup'))

        if len(username) < 4:
            flash('Username must be at least 4 characters', 'error')
            return redirect(url_for('signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return redirect(url_for('signup'))

        if users_collection.find_one({'username': username}):
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))

        if users_collection.find_one({'email': email}):
            flash('An account with that email already exists', 'error')
            return redirect(url_for('signup'))

        users_collection.insert_one({
            'username': username,
            'email': email,
            'password': generate_password_hash(password)
        })

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # allow either username or email
        query = {'username': identifier}
        if '@' in identifier:
            query = {'email': identifier.lower()}

        user_data = users_collection.find_one(query)

        if not user_data or not check_password_hash(user_data['password'], password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        user = User(user_data)
        login_user(user, remember=True)

        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('home_bp.dashboard'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


# -------------------- Password Reset Helpers --------------------

def _send_reset_email(to_addr, username, otp, reset_link):
    """Send a rich HTML + plain-text password reset email."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port   = os.getenv('SMTP_PORT')
    smtp_user   = os.getenv('SMTP_USER')
    smtp_pass   = os.getenv('SMTP_PASS')
    from_addr   = os.getenv('FROM_EMAIL', smtp_user or 'noreply@example.com')

    if not smtp_server or not smtp_port:
        print('[Email] SMTP config missing — email not sent')
        return False

    subject = 'PodcastAI Password Reset Verification'

    # ── Plain-text fallback ──────────────────────────────────────────────────
    plain = f"""Hello {username},

We received a request to reset the password for your PodcastAI account.

Your verification code is: {otp}

You can enter this code on the password reset page, or click the secure link
below to reset your password:

{reset_link}

This code and link will expire in 5 minutes.

If you did not request this password reset, please ignore this email.
Your account will remain secure.

Thank you,
PodcastAI Team"""

    current_year = datetime.now().year
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>PodcastAI Password Reset</title>
</head>
<body style="margin:0;padding:0;background:#0d0d14;font-family:'Segoe UI',Arial,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#0d0d14;padding:48px 0;">
    <tr><td align="center">

      <!-- Card -->
      <table width="580" cellpadding="0" cellspacing="0"
             style="background:#16162a;border-radius:18px;overflow:hidden;
                    border:1px solid rgba(139,92,246,.30);
                    box-shadow:0 20px 60px rgba(0,0,0,.5);">

        <!-- ═══ HEADER ═══ -->
        <tr>
          <td style="background:linear-gradient(135deg,#7c3aed 0%,#5b21b6 100%);
                     padding:36px 48px 30px;text-align:center;">
          <!-- Logo: pure CSS — works in all email clients, no image needed -->
            <table cellpadding="0" cellspacing="0" style="margin:0 auto;">
              <tr>
                <td valign="middle"
                    style="background:rgba(255,255,255,0.15);
                           border-radius:14px;
                           width:52px;height:52px;
                           text-align:center;line-height:52px;
                           font-size:26px;">
                  &#127897;
                </td>
                <td valign="middle"
                    style="padding-left:14px;
                           color:#ffffff;
                           font-size:26px;
                           font-weight:900;
                           letter-spacing:-0.5px;
                           font-family:'Segoe UI',Arial,sans-serif;">
                  PodcastAI
                </td>
              </tr>
            </table>
            <p style="color:rgba(255,255,255,.72);margin:14px 0 0;
                      font-size:14px;letter-spacing:.4px;">
              Password Reset Request
            </p>
          </td>
        </tr>

        <!-- ═══ BODY ═══ -->
        <tr>
          <td style="padding:44px 48px 36px;">

            <!-- Greeting -->
            <p style="color:#e2e8f0;font-size:17px;margin:0 0 6px;font-weight:600;">
              Hello <span style="color:#c084fc;">{username}</span>,
            </p>
            <p style="color:#94a3b8;font-size:15px;line-height:1.7;margin:0 0 32px;">
              We received a request to reset the password for your PodcastAI account.
              Use the verification code below or click the button to proceed.
            </p>

            <!-- ── OTP Box ── -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="margin-bottom:32px;">
              <tr>
                <td style="background:rgba(124,58,237,.12);
                           border:2px solid rgba(124,58,237,.45);
                           border-radius:14px;padding:28px 24px;text-align:center;">
                  <p style="color:#a78bfa;font-size:11px;margin:0 0 14px;
                            text-transform:uppercase;letter-spacing:2.5px;
                            font-weight:600;">
                    Your Verification Code
                  </p>
                  <!-- Large, bold, spaced OTP digits -->
                  <p style="color:#ede9fe;font-size:48px;font-weight:900;
                            letter-spacing:14px;font-family:monospace;
                            margin:0 0 16px;line-height:1;">
                    {otp}
                  </p>
                  <p style="color:#64748b;font-size:13px;margin:0;">
                    ⏱&nbsp;Expires in&nbsp;
                    <strong style="color:#f59e0b;">5 minutes</strong>
                  </p>
                </td>
              </tr>
            </table>

            <!-- Divider text -->
            <p style="color:#94a3b8;font-size:15px;line-height:1.7;margin:0 0 24px;">
              Or click the secure button below to reset your password directly:
            </p>

            <!-- ── CTA Button ── -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="margin-bottom:36px;">
              <tr>
                <td align="center">
                  <a href="{reset_link}"
                     style="display:inline-block;
                            background:linear-gradient(135deg,#7c3aed,#5b21b6);
                            color:#ffffff;text-decoration:none;
                            font-size:16px;font-weight:700;
                            padding:15px 44px;border-radius:50px;
                            letter-spacing:.3px;
                            box-shadow:0 6px 20px rgba(124,58,237,.50);">
                    Reset My Password
                  </a>
                </td>
              </tr>
            </table>

            <!-- ── Security Warning ── -->
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:rgba(239,68,68,.08);
                           border:1px solid rgba(239,68,68,.28);
                           border-left:4px solid #ef4444;
                           border-radius:10px;padding:16px 20px;">
                  <p style="color:#fca5a5;font-size:14px;margin:0;line-height:1.7;">
                    🔒&nbsp;<strong><em>Didn't request this?</em></strong>
                    &nbsp;If you did not request a password reset, please ignore this
                    email. Your account will remain secure and no changes will be made.
                  </p>
                </td>
              </tr>
            </table>

          </td>
        </tr>

        <!-- ═══ FOOTER ═══ -->
        <tr>
          <td style="background:#0d0d14;padding:22px 48px;text-align:center;
                     border-top:1px solid rgba(255,255,255,.06);">
            <p style="color:#475569;font-size:12px;margin:0 0 4px;line-height:1.7;">
              This link and code expire in 5 minutes.
            </p>
            <p style="color:#334155;font-size:12px;margin:0;">
              &copy; {current_year} PodcastAI &mdash; All rights reserved
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>

</body>
</html>"""

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'PodcastAI <{from_addr}>'
        msg['To']      = to_addr
        msg.attach(MIMEText(plain, 'plain'))
        msg.attach(MIMEText(html,  'html'))

        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.ehlo()
        server.starttls()
        server.ehlo()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
        print(f'[Email] Reset email sent to {to_addr}')
        return True
    except Exception as e:
        print(f'[Email] Error sending to {to_addr}:', e)
        return False


def _send_success_email(to_addr, username):
    """Notify the user their password was changed successfully."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port   = os.getenv('SMTP_PORT')
    smtp_user   = os.getenv('SMTP_USER')
    smtp_pass   = os.getenv('SMTP_PASS')
    from_addr   = os.getenv('FROM_EMAIL', smtp_user or 'noreply@example.com')
    if not smtp_server or not smtp_port:
        return
    subject = 'Your PodcastAI password has been updated'
    plain = (f'Hello {username},\n\nYour PodcastAI password was successfully changed.\n'
             f'If this wasn\'t you, contact support immediately.\n\nPodcastAI Team')
    try:
        msg = MIMEText(plain, 'plain')
        msg['Subject'] = subject
        msg['From']    = f'PodcastAI <{from_addr}>'
        msg['To']      = to_addr
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.ehlo(); server.starttls(); server.ehlo()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
    except Exception as e:
        print(f'[Email] Success-notification error: {e}')


# -------------------- Password Reset Routes --------------------

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email or '@' not in email:
            flash('Please provide a valid email address.', 'error')
            return render_template('forgot_password.html')

        user_data = users_collection.find_one({'email': email})
        if not user_data:
            # Generic message to avoid email enumeration
            flash('If that email is registered, a reset code has been sent.', 'success')
            return render_template('forgot_password.html')

        username   = user_data.get('username', 'there')
        otp        = str(secrets.randbelow(900000) + 100000)   # 6-digit secure OTP
        token      = secrets.token_hex(32)                      # 64-char hex token
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Remove any existing pending reset for this email
        password_resets_collection.delete_many({'email': email})

        # Store new reset record
        password_resets_collection.insert_one({
            'email':      email,
            'username':   username,
            'otp':        otp,
            'token':      token,
            'expires_at': expires_at,
            'verified':   False,
        })

        # Build reset link
        reset_link = url_for('reset_password', token=token, _external=True)

        # Send the email
        _send_reset_email(email, username, otp, reset_link)

        # Store only the email in session (no secrets)
        session['pr_email'] = email
        flash('A verification code has been sent to your email.', 'success')
        return redirect(url_for('verify_otp'))

    return render_template('forgot_password.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = session.get('pr_email')
    if not email:
        flash('Please start the password reset process first.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()

        record = password_resets_collection.find_one({'email': email, 'verified': False})
        if not record:
            flash('No pending reset request found. Please start again.', 'error')
            session.pop('pr_email', None)
            return redirect(url_for('forgot_password'))

        # Check expiry
        if datetime.now(timezone.utc) > record['expires_at'].replace(tzinfo=timezone.utc):
            password_resets_collection.delete_many({'email': email})
            session.pop('pr_email', None)
            flash('Your code has expired. Please request a new one.', 'error')
            return redirect(url_for('forgot_password'))

        # Check OTP
        if entered_otp != record['otp']:
            flash('Incorrect verification code. Please try again.', 'error')
            return render_template('verify_otp.html')

        # Mark as verified
        password_resets_collection.update_one(
            {'_id': record['_id']},
            {'$set': {'verified': True}}
        )
        session.pop('pr_email', None)
        return redirect(url_for('reset_password', token=record['token']))

    return render_template('verify_otp.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') or request.form.get('token', '')
    if not token:
        flash('Invalid or missing reset link.', 'error')
        return redirect(url_for('forgot_password'))

    record = password_resets_collection.find_one({'token': token})

    if not record:
        flash('This reset link is invalid or has already been used.', 'error')
        return redirect(url_for('forgot_password'))

    if datetime.now(timezone.utc) > record['expires_at'].replace(tzinfo=timezone.utc):
        password_resets_collection.delete_many({'email': record['email']})
        flash('This reset link has expired. Please start again.', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)

        # Update password
        users_collection.update_one(
            {'email': record['email']},
            {'$set': {'password': generate_password_hash(new_password)}}
        )

        # Delete reset record (used up)
        password_resets_collection.delete_many({'email': record['email']})

        # Send confirmation email
        _send_success_email(record['email'], record.get('username', 'there'))

        flash('Password reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

# -------------------- Backwards Compatibility --------------------
@app.route('/home')
@login_required
def home_redirect():
    return redirect(url_for('home_bp.dashboard'))


# -------------------- Blueprint --------------------
app.register_blueprint(home_bp)


if __name__ == '__main__':
    app.run(debug=True)
