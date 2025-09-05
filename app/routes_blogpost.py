from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app import db
from app.models import BlogPost

# Create a blueprint for main routes
blogpost_bp = Blueprint('blogpost_bp', __name__)

# Route to view a single blog post
@blogpost_bp.route('/post/<int:post_id>')
def view_post(post_id):
    # Query the specific blog post by ID
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)

# Route to create a new blog post
@blogpost_bp.route('/new', methods=['POST'])
@login_required
def new_post():
    form = BlogPostForm()
    
    # save portrait to uploads dir
    
    # downsize & save a thumbnail to the same dir
    
    # only commit the name(s) to the db...
    
    
    if form.validate_on_submit():
        # Create a new blog post object
        post = BlogPost(
            title=form.title.data,
            content=form.content.data,
            portrait=form.portrait.data # FIXME pull the name from the file data
        )
        # Add the new post to the database
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main_bp.index'))
    return render_template('new_post.html', form=form)
