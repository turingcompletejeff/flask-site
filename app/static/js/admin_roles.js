/**
 * Admin Roles Management JavaScript - In-line Editing
 *
 * Handles in-line editing for role management with AJAX updates.
 * Uses jQuery and the global addFlashMessage function from layout.html.
 */

$(function() {
    // ========== State Management ==========
    let currentlyEditingRowId = null;
    const originalRowData = new Map();

    // ========== Edit Mode Functions ==========

    /**
     * Enter edit mode for a specific role row
     * @param {number} roleId - The role ID
     */
    function enterEditMode(roleId) {
        // Prevent editing multiple rows at once
        if (currentlyEditingRowId !== null) {
            addFlashMessage('warning', 'Please save or cancel the current edit before editing another role.');
            return;
        }

        const $row = $(`.role-row[data-role-id="${roleId}"]`);

        // Store original values
        const originalData = {
            name: $row.find('.role-name-display').text(),
            description: $row.find('.role-description-display').text() === 'No description'
                ? ''
                : $row.find('.role-description-display').text(),
            badgeColor: $row.find('.role-color-picker').val()
        };
        originalRowData.set(roleId, originalData);

        // Switch to edit mode
        $row.addClass('editing');

        // Toggle display/input elements
        $row.find('.role-name-display').hide();
        $row.find('.role-name-input').show().focus();

        $row.find('.role-description-display').hide();
        $row.find('.role-description-input').show();

        // Enable color picker
        $row.find('.role-color-picker').prop('disabled', false);

        // Toggle action buttons
        $row.find('.view-mode-actions').hide();
        $row.find('.edit-mode-actions').show();

        // Disable edit/delete buttons in other rows
        $('.role-row').not($row).find('.edit-role-btn, .delete-role-btn').prop('disabled', true);

        // Track current editing row
        currentlyEditingRowId = roleId;
    }

    /**
     * Exit edit mode without saving (restore original values)
     * @param {number} roleId - The role ID
     */
    function exitEditMode(roleId) {
        const $row = $(`.role-row[data-role-id="${roleId}"]`);
        const original = originalRowData.get(roleId);

        if (!original) return;

        // Restore original values
        $row.find('.role-name-input').val(original.name);
        $row.find('.role-description-input').val(original.description);
        $row.find('.role-color-picker').val(original.badgeColor);
        $row.find('.color-hex').text(original.badgeColor);
        $row.find('.role-badge-preview').css('background-color', original.badgeColor);
        $row.find('.role-badge-preview').text(original.name);

        // Clear any error states
        $row.find('.role-name-input, .role-description-input').removeClass('error');

        // Switch back to view mode
        $row.removeClass('editing');

        // Toggle display/input elements
        $row.find('.role-name-display').show();
        $row.find('.role-name-input').hide();

        $row.find('.role-description-display').show();
        $row.find('.role-description-input').hide();

        // Disable color picker
        $row.find('.role-color-picker').prop('disabled', true);

        // Toggle action buttons
        $row.find('.view-mode-actions').show();
        $row.find('.edit-mode-actions').hide();

        // Re-enable edit/delete buttons in other rows
        $('.edit-role-btn, .delete-role-btn').prop('disabled', false);

        // Clear tracking
        currentlyEditingRowId = null;
        originalRowData.delete(roleId);
    }

    /**
     * Validate role input fields
     * @param {number} roleId - The role ID
     * @returns {Object} - { valid: boolean, errors: array }
     */
    function validateRoleInput(roleId) {
        const $row = $(`.role-row[data-role-id="${roleId}"]`);
        const errors = [];

        // Get values
        const name = $row.find('.role-name-input').val().trim();
        const badgeColor = $row.find('.role-color-picker').val();

        // Clear previous error states
        $row.find('.role-name-input, .role-description-input').removeClass('error');

        // Validate name (required, 2-50 chars)
        if (!name || name.length < 2) {
            errors.push('Role name must be at least 2 characters');
            $row.find('.role-name-input').addClass('error');
        } else if (name.length > 50) {
            errors.push('Role name must not exceed 50 characters');
            $row.find('.role-name-input').addClass('error');
        }

        // Validate hex color format
        const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
        if (!hexColorRegex.test(badgeColor)) {
            errors.push('Invalid color format');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Save role changes via AJAX
     * @param {number} roleId - The role ID
     */
    function saveRoleChanges(roleId) {
        // Validate first
        const validation = validateRoleInput(roleId);
        if (!validation.valid) {
            addFlashMessage('danger', validation.errors.join(', '));
            return;
        }

        const $row = $(`.role-row[data-role-id="${roleId}"]`);
        const $saveBtn = $row.find('.save-role-btn');

        // Get new values
        const newData = {
            role_id: roleId,
            name: $row.find('.role-name-input').val().trim(),
            description: $row.find('.role-description-input').val().trim(),
            badge_color: $row.find('.role-color-picker').val()
        };

        // Disable save/cancel buttons during request
        $saveBtn.prop('disabled', true);
        $row.find('.cancel-edit-btn').prop('disabled', true);

        // Visual feedback
        const originalIcon = $saveBtn.find('.material-symbols-outlined').text();
        $saveBtn.find('.material-symbols-outlined').text('hourglass_empty');

        $.ajax({
            url: '/admin/update_role',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newData),
            success: function(response) {
                if (response.status === 'success') {
                    // Update display elements with new values
                    $row.find('.role-name-display').text(newData.name);
                    $row.find('.role-description-display').text(
                        newData.description || 'No description'
                    );
                    $row.find('.role-badge-preview').text(newData.name);

                    // Update original color data attribute
                    $row.find('.role-color-picker').data('original-color', newData.badge_color);

                    // Exit edit mode
                    exitEditMode(roleId);

                    // Show success message
                    addFlashMessage('success', 'Role updated successfully!');
                } else {
                    addFlashMessage('danger', response.message || 'Failed to update role');
                    restoreButton();
                }
            },
            error: function(xhr) {
                let errorMsg = 'Network error occurred';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                addFlashMessage('danger', errorMsg);
                restoreButton();
            }
        });

        function restoreButton() {
            $saveBtn.prop('disabled', false);
            $row.find('.cancel-edit-btn').prop('disabled', false);
            $saveBtn.find('.material-symbols-outlined').text(originalIcon);
        }
    }

    // ========== Event Handlers ==========

    // Edit button click - enter edit mode
    $(document).on('click', '.edit-role-btn', function() {
        const roleId = $(this).data('role-id');
        enterEditMode(roleId);
    });

    // Save button click - save changes
    $(document).on('click', '.save-role-btn', function() {
        const roleId = $(this).data('role-id');
        saveRoleChanges(roleId);
    });

    // Cancel button click - exit without saving
    $(document).on('click', '.cancel-edit-btn', function() {
        const roleId = $(this).data('role-id');
        exitEditMode(roleId);
    });

    // Escape key - cancel edit mode
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && currentlyEditingRowId !== null) {
            exitEditMode(currentlyEditingRowId);
        }
    });

    // Color picker change - update preview live
    $(document).on('input', '.role-color-picker', function() {
        const $row = $(this).closest('.role-row');
        const newColor = $(this).val();

        // Update hex display and preview
        $row.find('.color-hex').text(newColor);
        $row.find('.role-badge-preview').css('background-color', newColor);
    });

    // Enter key in name input - save
    $(document).on('keydown', '.role-name-input', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const roleId = $(this).closest('.role-row').data('role-id');
            saveRoleChanges(roleId);
        }
    });

    // ========== Delete Role Modal Handling ==========

    const $deleteModal = $('#deleteRoleModal');
    const $deleteForm = $('#deleteRoleForm');
    const $deleteMessage = $('#deleteRoleMessage');

    // Handle delete button clicks
    $('.delete-role-btn').on('click', function() {
        const roleId = $(this).data('role-id');
        const roleName = $(this).data('role-name');
        const userCount = $(this).data('user-count');

        // Set the form action to the delete URL
        $deleteForm.attr('action', `/admin/roles/${roleId}/delete`);

        // Set the confirmation message
        if (userCount > 0) {
            $deleteMessage.html(
                `<strong>Warning:</strong> Cannot delete role "<strong>${roleName}</strong>" - ` +
                `it is currently assigned to <strong>${userCount}</strong> user(s).<br><br>` +
                `Please remove this role from all users before deleting it.`
            );
            // Disable the delete button
            $deleteForm.find('button[type="submit"]').prop('disabled', true);
        } else {
            $deleteMessage.html(
                `Are you sure you want to delete the role "<strong>${roleName}</strong>"?<br><br>` +
                `This action cannot be undone.`
            );
            // Enable the delete button
            $deleteForm.find('button[type="submit"]').prop('disabled', false);
        }

        // Show the modal
        $deleteModal.fadeIn(200);
    });

    // Handle cancel button and overlay clicks
    $('.cancel-delete-btn, .modal-overlay').on('click', function() {
        $deleteModal.fadeOut(200);
    });

    // Close modal on escape key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape' && $deleteModal.is(':visible')) {
            $deleteModal.fadeOut(200);
        }
    });
});
