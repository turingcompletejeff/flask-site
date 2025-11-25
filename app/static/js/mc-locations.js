/**
 * Minecraft Locations Management
 * Handles location CRUD operations, inline form display, and AJAX submissions
 */

$(document).ready(function() {
    // Load locations on page load
    loadLocations();

    // Show/hide create form
    $('#btn-new-location').on('click', showCreateForm);
    $('#btn-cancel-form, #btn-cancel-create').on('click', hideCreateForm);

    // Handle form submission
    $('#new-location-form').on('submit', handleCreateSubmit);

    // Location card expand/collapse (delegated event)
    $(document).on('click', '.location-card h3', toggleLocationDetails);

    // Edit/Delete actions (delegated events)
    $(document).on('click', '.btn-edit-location', handleEditClick);
    $(document).on('click', '.btn-delete-location', handleDeleteClick);
});

/**
 * Load all locations via AJAX
 */
function loadLocations() {
    $.ajax({
        url: MC_ENDPOINTS.locations,
        method: 'GET',
        dataType: 'json',
        success: function(locations) {
            displayLocations(locations);
        },
        error: function(xhr, status, error) {
            console.error('Failed to load locations:', error);
            $('#locations-grid').html(
                '<p class="error">Failed to load locations. Please try again.</p>'
            );
        }
    });
}

/**
 * Display locations in grid
 */
function displayLocations(locations) {
    const $grid = $('#locations-grid');

    if (locations.length === 0) {
        $grid.html('<p class="no-locations">No locations yet. Create one to get started!</p>');
        return;
    }

    const locationsHTML = locations.map(function(location) {
        const thumbnailUrl = `${MC_ENDPOINTS.uploadedFiles}/${location.thumbnail}`;
        const description = location.description || 'No description';

        const actionButtons = IS_USER_MINECRAFTER ? `
            <div class="location-actions">
                <button type="button" class="clicky-secondary btn-edit-location" data-location-id="${location.id}">
                    Edit
                </button>
                <button type="button" class="clicky-danger btn-delete-location" data-location-id="${location.id}">
                    Delete
                </button>
            </div>
        ` : '';

        return `
            <div class="location-card" data-location-id="${location.id}">
                <div class="location-thumbnail" style="background-image: url('${thumbnailUrl}')">
                </div>
                <div class="location-content">
                    <h3>
                        ${escapeHtml(location.name)}
                        <span class="expand-arrow">▼</span>
                    </h3>
                    <div class="location-details" style="display: none;">
                        <p class="description">${escapeHtml(description)}</p>
                        <p class="coordinates">
                            <strong>Coordinates:</strong>
                            (${location.position.x}, ${location.position.y}, ${location.position.z})
                        </p>
                        ${actionButtons}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    $grid.html(locationsHTML);
}

/**
 * Toggle location details expand/collapse
 */
function toggleLocationDetails() {
    const $details = $(this).siblings('.location-details');
    const $arrow = $(this).find('.expand-arrow');

    $details.slideToggle(200, function() {
        if ($details.is(':visible')) {
            $arrow.text('▲');
        } else {
            $arrow.text('▼');
        }
    });
}

/**
 * Show create location form
 */
function showCreateForm() {
    $('#new-location-form-container').slideDown(300);
    $('#btn-new-location').prop('disabled', true);
    // Focus first field
    $('#name').focus();
}

/**
 * Hide create location form and reset
 */
function hideCreateForm() {
    $('#new-location-form-container').slideUp(300);
    $('#btn-new-location').prop('disabled', false);
    resetCreateForm();
}

/**
 * Reset create form fields and errors
 */
function resetCreateForm() {
    $('#new-location-form')[0].reset();
    $('#form-errors').hide().empty();
    $('.form__error').remove();
}

/**
 * Handle create form submission via AJAX
 */
function handleCreateSubmit(e) {
    e.preventDefault();

    // Clear previous errors
    $('#form-errors').hide().empty();
    $('.form__error').remove();

    // Get form data
    const formData = new FormData(this);

    // Disable submit button during request
    const $submitBtn = $(this).find('button[type="submit"]');
    $submitBtn.prop('disabled', true).text('Creating...');

    $.ajax({
        url: MC_ENDPOINTS.createLocation,
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                // Show success message
                showFlashMessage(response.message || 'Location created!', 'success');

                // Hide form and reload locations
                hideCreateForm();
                loadLocations();
            } else {
                // Display validation errors
                displayFormErrors(response.errors);
            }
        },
        error: function(xhr, status, error) {
            console.error('Create location failed:', error);
            let errorMsg = 'Failed to create location. Please try again.';

            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg = xhr.responseJSON.message;
            }

            showFlashMessage(errorMsg, 'danger');
        },
        complete: function() {
            // Re-enable submit button
            $submitBtn.prop('disabled', false).html('<span class="btn-icon">✓</span> Create Location');
        }
    });
}

/**
 * Display form validation errors
 */
function displayFormErrors(errors) {
    if (!errors || typeof errors !== 'object') return;

    const $errorContainer = $('#form-errors');
    const errorMessages = [];

    // Iterate through field errors
    for (const [field, messages] of Object.entries(errors)) {
        const $field = $(`#${field}`);

        if (Array.isArray(messages)) {
            messages.forEach(function(msg) {
                // Add error to field
                if ($field.length) {
                    $field.closest('.form__group').append(
                        `<span class="form__error">${escapeHtml(msg)}</span>`
                    );
                }
                errorMessages.push(msg);
            });
        }
    }

    // Display errors in container
    if (errorMessages.length > 0) {
        $errorContainer.html(
            '<strong>Please fix the following errors:</strong><ul>' +
            errorMessages.map(msg => `<li>${escapeHtml(msg)}</li>`).join('') +
            '</ul>'
        ).show();
    }
}

/**
 * Handle edit button click
 */
function handleEditClick() {
    const locationId = $(this).data('location-id');
    window.location.href = MC_ENDPOINTS.editLocation(locationId);
}

/**
 * Handle delete button click
 */
function handleDeleteClick() {
    const locationId = $(this).data('location-id');
    const $card = $(this).closest('.location-card');
    const locationName = $card.find('h3').text().replace('▼', '').replace('▲', '').trim();

    if (!confirm(`Are you sure you want to delete "${locationName}"? This cannot be undone.`)) {
        return;
    }

    // Disable delete button
    const $deleteBtn = $(this);
    $deleteBtn.prop('disabled', true).text('Deleting...');

    $.ajax({
        url: MC_ENDPOINTS.deleteLocation(locationId),
        method: 'POST',
        headers: {
            'X-CSRFToken': $('meta[name="csrf-token"]').attr('content')
        },
        dataType: 'json',
        success: function(response) {
            if (response.success) {
                showFlashMessage(response.message || 'Location deleted!', 'success');

                // Fade out and remove card
                $card.fadeOut(300, function() {
                    $(this).remove();

                    // Check if no locations remain
                    if ($('.location-card').length === 0) {
                        $('#locations-grid').html(
                            '<p class="no-locations">No locations yet. Create one to get started!</p>'
                        );
                    }
                });
            } else {
                showFlashMessage(response.message || 'Failed to delete location.', 'danger');
                $deleteBtn.prop('disabled', false).text('Delete');
            }
        },
        error: function(xhr, status, error) {
            console.error('Delete location failed:', error);
            showFlashMessage('Failed to delete location. Please try again.', 'danger');
            $deleteBtn.prop('disabled', false).text('Delete');
        }
    });
}

/**
 * Show flash message (mimics Flask flash messages)
 */
function showFlashMessage(message, category) {
    const categoryClass = category === 'success' ? 'alert-success' : 'alert-danger';

    const $alert = $(`
        <div class="alert ${categoryClass} alert-dismissible fade show" role="alert">
            ${escapeHtml(message)}
            <button type="button" class="btn-close" aria-label="Close">&times;</button>
        </div>
    `);

    // Find or create flash container
    let $flashContainer = $('.flash-messages');
    if ($flashContainer.length === 0) {
        $flashContainer = $('<div class="flash-messages"></div>');
        $('#locations-section').prepend($flashContainer);
    }

    $flashContainer.append($alert);

    // Auto-dismiss after 5 seconds
    setTimeout(function() {
        $alert.fadeOut(300, function() {
            $(this).remove();
        });
    }, 5000);

    // Manual dismiss
    $alert.find('.btn-close').on('click', function() {
        $alert.fadeOut(300, function() {
            $(this).remove();
        });
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, function(m) { return map[m]; });
}
