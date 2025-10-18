from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, jsonify
from app import db
from app.models import BlogPost
from app.forms import ContactForm
from config import Config
import smtplib
from email.message import EmailMessage

# Create a blueprint for main routes
main = Blueprint('main', __name__)

# Home page
@main.route('/')
def index():
    from flask_login import current_user
    msg = request.args.get("flash")
    cat = request.args.get("category", "info")
    if msg:
        flash(msg, cat)

    # Query blog posts based on authentication status
    if current_user.is_authenticated:
        # Authenticated users see all posts (drafts + published)
        blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc(),BlogPost.id.desc()).all()
    else:
        # Public users only see published posts
        blog_posts = BlogPost.query.filter_by(is_draft=False).order_by(BlogPost.date_posted.desc(),BlogPost.id.desc()).all()

    return render_template('index.html', blog_posts=blog_posts, current_page="blog")

# About page
@main.route('/about')
def about():
    return render_template('about.html', current_page="about")
    
# Contact form
@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    if form.validate_on_submit():
        try:
            # process the data, send an email
            message = formatContactEmail(form)
            current_app.logger.info('Attempting to send contact form message')
            current_app.logger.info(f'Message content: {message}')
            current_app.logger.info(f'From: {Config.MAIL_USER}')
            current_app.logger.info(f'To: {Config.ADMIN_EMAIL}')
            current_app.logger.info('Sending email...')
            sendAnEmail(message)

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({
                    'success': True,
                    'message': f'message sent from {form.email.data}',
                    'redirect': url_for('main.index')
                })
            else:
                flash(f'message sent from {form.email.data}', "success")
                return redirect(url_for('main.index'))

        except Exception as e:
            current_app.logger.error(f'Error sending email: {e}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': 'Failed to send message. Please try again.'}), 500
            else:
                flash('Failed to send message. Please try again.', 'error')
                return render_template('contact.html', current_page="contact", form=form)

    # If form has validation errors and it's an AJAX request, return the form with errors
    if request.method == 'POST' and (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', '')):
        current_app.logger.warning(f"Form validation failed. Errors: {form.errors}")
        return render_template('contact.html', current_page="contact", form=form)

    return render_template('contact.html', current_page="contact", form=form)

@main.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)

# formats the user's form contents as an email message
def formatContactEmail(contactForm):
    return f'a person has contacted you from the site form:\n' \
           f'----------------------------------------------\n' \
           f'name: {contactForm.name.data}\n' \
           f'email: {contactForm.email.data}\n' \
           f'phone: {contactForm.phone.data}\n' \
           f'reason: {contactForm.reason.data}\n' \
           f'message: {contactForm.message.data}\n'

# DIRECTLY sends an email, set up from an auto mailer acct
def sendAnEmail(message):
    # send email FROM a site-specific mailer acct
    from_addr = Config.MAIL_USER
    # send email TO the site admin's email
    to_addr = [Config.ADMIN_EMAIL]
    
    # connect to SMTP
    smtp = smtplib.SMTP()
    smtp._host = Config.MAIL_SERVER
    smtp.connect(Config.MAIL_SERVER, Config.MAIL_PORT)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    smtp.login(Config.MAIL_USER, Config.MAIL_PW)
    
    # set up email
    email = EmailMessage()
    email['Subject'] = f'- automail contact form -'
    email['From'] = from_addr
    email['To'] = to_addr
    # attach message w/ no extra formatting
    email.set_content(message)
    
    smtp.sendmail(from_addr,to_addr,email.as_string())
    smtp.quit()

# tests smtp credentials for auto-mailer,server,port
def attemptEmailConnection():
    # connect to SMTP
    current_app.logger.info(f'Opening SMTP connection on {Config.MAIL_SERVER}:{Config.MAIL_PORT}')
    smtp = smtplib.SMTP()
    smtp._host = Config.MAIL_SERVER
    smtp.set_debuglevel(100) # just for demo purpose
    smtp.connect(Config.MAIL_SERVER, Config.MAIL_PORT)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    current_app.logger.info('Attempting SMTP login...')
    smtp.login(Config.MAIL_USER, Config.MAIL_PW)
    current_app.logger.info('Closing SMTP connection')
    smtp.quit()
    current_app.logger.info('SMTP connection test successful')
    return True
