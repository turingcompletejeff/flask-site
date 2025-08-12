# Route to view a single blog post
@main_bp.route('/post/<int:post_id>')
def view_post(post_id):
    # Query the specific blog post by ID
    post = BlogPost.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)

# Route to create a new blog post
@main_bp.route('/new', methods=['GET', 'POST'])
def new_post():
    form = BlogPostForm()
    if form.validate_on_submit():
        # Create a new blog post object
        post = BlogPost(
            title=form.title.data,
            content=form.content.data
        )
        # Add the new post to the database
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main_bp.index'))
    return render_template('new_post.html', form=form)

# Route to edit an existing blog post
@main_bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm()

    # Populate the form with the existing post data
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    # Update the post if the form is submitted and valid
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('main_bp.view_post', post_id=post.id))

    return render_template('edit_post.html', form=form, post=post)

# Route to delete a blog post
@main_bp.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('main_bp.index'))