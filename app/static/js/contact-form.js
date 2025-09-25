$(document).ready(function() {
    initContactFormHandlers();
});

function initContactFormHandlers() {
    const $form = $('form[action="/contact"]');

    if ($form.length === 0) return; // No contact form on this page

    const $submitBtn = $('.form__submit');
    const $formFields = $form.find('input, textarea, select');

    // Remove any existing spinner to avoid duplicates
    $('#form-spinner').remove();

    // Create and insert loading spinner
    const $spinner = $('<div id="form-spinner" class="spinner-overlay" style="display: none;">' +
                      '<div class="spinner-container">' +
                      '<span class="material-symbols-outlined spinner" id="contact-spinner">refresh</span>' +
                      '<div class="loading-text">sending message...</div>' +
                      '</div>' +
                      '</div>');

    $form.parent('.blog-post').prepend($spinner);

    // Remove any existing submit handlers to avoid duplicates
    $form.off('submit.contactForm');

    $form.on('submit.contactForm', function(e) {
        e.preventDefault();
        
        // Capture form data BEFORE disabling the form
        const formData = new FormData(this);

        // Show spinner and disable form
        showLoadingState();

        $.ajax({
            url: '/contact',
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': $("meta[name=csrf-token]").attr("content")
            },
            success: function(response) {
                if (typeof response === 'object' && response.success) {
                    // JSON response - success
                    addFlashMessage('success', 'Message sent successfully!');

                    // Smooth transition to home page
                    setTimeout(function() {
                        window.location.href = response.redirect || '/';
                    }, 1500);
                } else if (typeof response === 'string') {
                    // HTML response - form has errors
                    hideLoadingState();

                    // Replace the current content with the new form that has validation errors
                    const $newContent = $(response).find('.content').html();
                    $('.content').html($newContent);

                    // Re-initialize form handling for the new content
                    initContactFormHandlers();
                } else {
                    // Unexpected response
                    hideLoadingState();
                    addFlashMessage('error', 'Unexpected response. Please try again.');
                }
            },
            error: function(xhr, status, error) {
                hideLoadingState();

                if (xhr.responseJSON && xhr.responseJSON.error) {
                    addFlashMessage('error', xhr.responseJSON.error);
                } else {
                    addFlashMessage('error', 'Failed to send message. Please try again.');
                }
            }
        });
    });

    function showLoadingState() {
        $spinner.fadeIn(300);
        $submitBtn.prop('disabled', true);
        $formFields.prop('disabled', true);
        $form.addClass('form-disabled');
    }

    function hideLoadingState() {
        $spinner.fadeOut(300);
        $submitBtn.prop('disabled', false);
        $formFields.prop('disabled', false);
        $form.removeClass('form-disabled');
    }
}