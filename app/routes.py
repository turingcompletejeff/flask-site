from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from app import db
from app.models import BlogPost
from app.forms import ContactForm
from config import Config
import smptlib
from email.message import EmailMessage

# Create a blueprint for main routes
main_bp = Blueprint('main_bp', __name__)

# Home page
@main_bp.route('/')
def index():
    msg = request.args.get("flash")
    cat = request.args.get("category", "info")
    if msg:
        flash(msg, cat)
    # Query all blog posts in descending order by date
    blog_posts = BlogPost.query.order_by(BlogPost.date_posted.desc(),BlogPost.id.desc()).all()
    
    return render_template('index.html', blog_posts=blog_posts, current_page="blog")

# About page
@main_bp.route('/about')
def about():
    return render_template('about.html', current_page="about")
    
# Contact form
@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    
    if form.validate_on_submit()
        # process the data, send an email
        message = formatContactEmail(form)
        print('dry run. attempting to send message:')
        print(message)
        print(f'from: {Config.MAIL_USER}')
        print(f'to: {Config.ADMIN_EMAIL}')
        print('testing connection...')
        attemptEmailConnection()
        
        flash(f'message ~(FIXME) NOT~ sent from {form.email.data}', "success")
        return redirect(url_for('main_bp.contact'))
    
    return render_template('contact.html', current_page="contact", form=form)

@main_bp.route('/uploads/blog-posts/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['BLOG_POST_UPLOAD_FOLDER'], filename)

# formats the user's form contents as an email message
def formatContactEmail(contactForm):
    return f'a person has contacted you from the site form:\n'
           f'----------------------------------------------\n'
           f'name: {contactForm.name.data}\n'
           f'email: {contactForm.email.data}\n'
           f'reason: {contactForm.reason.data}\n'
           f'message: {contactForm.message.data}\n'

# DIRECTLY sends an email, set up from an auto mailer acct
def sendAnEmail(message):
    # send email FROM a site-specific mailer acct
    from_addr = Config.MAIL_USER
    # send email TO the site admin's email
    to_addr = [Config.ADMIN_EMAIL]
    
    # connect to SMTP
    smtp = SMTP()
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
    
    smtp.sendmail(email)
    smtp.quit()

# tests smtp credentials for auto-mailer,server,port
def attemptEmailConnection():
    # connect to SMTP
    print('opening connection...')
    smtp = SMTP()
    smtp.connect(Config.MAIL_SERVER, Config.MAIL_PORT)
    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()
    print('attempting login...')
    smtp.login(Config.MAIL_USER, Config.MAIL_PW)
    print('quitting.')
    smtp.quit()
    print('success!')
    return True