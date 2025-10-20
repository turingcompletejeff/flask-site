/**
 * Admin Roles Management JavaScript - In-line Editing
 *
 * Handles in-line editing for role management with AJAX updates.
 * Uses jQuery and the global addFlashMessage function from layout.html.
 */

$(function() {
    // ========== State Management ==========
    let currentlyEditingRowId = null;
    let isCreatingRole = false;
    const originalRowData = new Map();

    // ========== Edit Mode Functions ==========

    /**
     * Enter edit mode for a specific role row
     * @param {number} roleId - The role ID
     */
    function enterEditMode(roleId) {
        // Guard: prevent editing during creation
        if (isCreatingRole) {
            addFlashMessage('warning', 'Please save or cancel the new role before editing another role.');
            return;
        }

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
     * Exit edit mode
     * @param {number} roleId - The role ID
     * @param {boolean} restoreValues - Whether to restore original values (default: true)
     */
    function exitEditMode(roleId, restoreValues = true) {
        const $row = $(`.role-row[data-role-id="${roleId}"]`);
        const original = originalRowData.get(roleId);

        if (!original) return;

        // Restore original values only when canceling (not when saving)
        if (restoreValues) {
            $row.find('.role-name-input').val(original.name);
            $row.find('.role-description-input').val(original.description);
            $row.find('.role-color-picker').val(original.badgeColor);
            $row.find('.color-hex').text(original.badgeColor);
            $row.find('.role-badge-preview').css('background-color', original.badgeColor);
            $row.find('.role-badge-preview').text(original.name);
        }

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

                    // Update input elements with new values (critical for subsequent edits)
                    $row.find('.role-name-input').val(newData.name);
                    $row.find('.role-description-input').val(newData.description);
                    $row.find('.role-color-picker').val(newData.badge_color);
                    $row.find('.color-hex').text(newData.badge_color);
                    $row.find('.role-badge-preview').css('background-color', newData.badge_color);

                    // Update original color data attribute
                    $row.find('.role-color-picker').data('original-color', newData.badge_color);

                    // Restore button state before exiting edit mode
                    restoreButton();

                    // Exit edit mode (don't restore values - we just saved them)
                    exitEditMode(roleId, false);

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

    // ========== Creation Mode Functions ==========

    /**
     * Enter creation mode - insert new editable row
     */
    function enterCreationMode() {
        // Guard: prevent multiple creations
        if (isCreatingRole) {
            addFlashMessage('warning', 'You are already creating a role.');
            return;
        }

        // Guard: prevent creation during edit
        if (currentlyEditingRowId !== null) {
            addFlashMessage('warning', 'Please save or cancel the current edit before creating a new role.');
            return;
        }

        // Build creation row HTML
        const $creationRow = $(`
            <tr class="role-row creating-role editing" data-role-id="new">
                <td>
                    <input type="text"
                           class="role-name-input new-role-name"
                           placeholder="Enter role name..."
                           maxlength="50">
                </td>
                <td>
                    <textarea class="role-description-input new-role-description"
                              placeholder="Enter description (optional)..."
                              maxlength="200"></textarea>
                </td>
                <td>
                    <input type="color"
                           class="role-color-picker new-role-color"
                           value="#58cc02">
                    <span class="color-hex">#58cc02</span>
                </td>
                <td>
                    <span class="role-badge-preview"
                          style="background-color: #58cc02;">
                        Role Name
                    </span>
                </td>
                <td class="actions-cell">
                    <div class="edit-mode-actions">
                        <button type="button"
                                class="btn-icon save-new-role-btn"
                                title="Save">
                            <span class="material-symbols-outlined">check</span>
                        </button>
                        <button type="button"
                                class="btn-icon cancel-new-role-btn"
                                title="Cancel">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                </td>
            </tr>
        `);

        // Insert before the "add-role-row"
        $('.add-role-row').before($creationRow);

        // Hide the "Create New Role" button
        $('.add-role-btn').hide();

        // Disable edit/delete buttons on existing rows
        $('.role-row').not('.creating-role').find('.edit-role-btn, .delete-role-btn').prop('disabled', true);

        // Focus on name input
        $('.new-role-name').focus();

        // Set state flag
        isCreatingRole = true;
    }

    /**
     * Exit creation mode - remove creation row and restore UI
     */
    function exitCreationMode() {
        // Remove the creation row from DOM
        $('.creating-role').remove();

        // Show the "Create New Role" button
        $('.add-role-btn').show();

        // Re-enable edit/delete buttons on existing rows
        $('.edit-role-btn, .delete-role-btn').prop('disabled', false);

        // Clear state flag
        isCreatingRole = false;
    }

    /**
     * Validate new role input
     * @returns {Object} - { valid: boolean, errors: array }
     */
    function validateNewRole() {
        const name = $('.new-role-name').val().trim();
        const description = $('.new-role-description').val().trim();
        const color = $('.new-role-color').val();
        const errors = [];

        // Clear previous errors
        $('.new-role-name, .new-role-description').removeClass('error');

        // Name validation
        if (!name || name.length < 2) {
            errors.push('Role name must be at least 2 characters');
            $('.new-role-name').addClass('error');
        } else if (name.length > 50) {
            errors.push('Role name must not exceed 50 characters');
            $('.new-role-name').addClass('error');
        }

        // Description validation
        if (description && description.length > 200) {
            errors.push('Description must not exceed 200 characters');
            $('.new-role-description').addClass('error');
        }

        // Color validation
        const hexColorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
        if (!hexColorRegex.test(color)) {
            errors.push('Invalid color format');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Save new role via AJAX
     */
    function saveNewRole() {
        // Validate first
        const validation = validateNewRole();
        if (!validation.valid) {
            addFlashMessage('danger', validation.errors.join(', '));
            return;
        }

        const $saveBtn = $('.save-new-role-btn');
        const $cancelBtn = $('.cancel-new-role-btn');

        // Get values
        const newData = {
            name: $('.new-role-name').val().trim(),
            description: $('.new-role-description').val().trim(),
            badge_color: $('.new-role-color').val()
        };

        // Disable buttons during request
        $saveBtn.prop('disabled', true);
        $cancelBtn.prop('disabled', true);

        // Visual feedback
        const originalIcon = $saveBtn.find('.material-symbols-outlined').text();
        $saveBtn.find('.material-symbols-outlined').text('hourglass_empty');

        $.ajax({
            url: '/admin/roles/create',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newData),
            success: function(response) {
                if (response.status === 'success') {
                    // Build new role row HTML with data from server
                    const role = response.role;
                    const $newRow = $(`
                        <tr data-role-id="${role.id}" class="role-row">
                            <td>
                                <strong class="role-name-display">${role.name}</strong>
                                <input type="text"
                                       class="role-name-input"
                                       value="${role.name}"
                                       style="display: none;">
                            </td>
                            <td>
                                <span class="role-description-display">${role.description || 'No description'}</span>
                                <textarea class="role-description-input"
                                          style="display: none;">${role.description || ''}</textarea>
                            </td>
                            <td>
                                <input type="color"
                                       class="role-color-picker"
                                       id="color-${role.id}"
                                       value="${role.badge_color}"
                                       data-role-id="${role.id}"
                                       data-original-color="${role.badge_color}"
                                       disabled>
                                <span class="color-hex" id="hex-${role.id}">${role.badge_color}</span>
                            </td>
                            <td>
                                <span class="role-badge-preview"
                                      id="preview-${role.id}"
                                      style="background-color: ${role.badge_color};">
                                    ${role.name}
                                </span>
                            </td>
                            <td class="actions-cell">
                                <div class="view-mode-actions">
                                    <button type="button"
                                            class="btn-icon edit-role-btn"
                                            data-role-id="${role.id}"
                                            title="Edit role">
                                        <span class="material-symbols-outlined">edit</span>
                                    </button>
                                    <button type="button"
                                            class="btn-icon delete-role-btn"
                                            data-role-id="${role.id}"
                                            data-role-name="${role.name}"
                                            data-user-count="0"
                                            title="Delete role">
                                        <span class="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                                <div class="edit-mode-actions" style="display: none;">
                                    <button type="button"
                                            class="btn-icon save-role-btn"
                                            data-role-id="${role.id}"
                                            title="Save">
                                        <span class="material-symbols-outlined">check</span>
                                    </button>
                                    <button type="button"
                                            class="btn-icon cancel-edit-btn"
                                            data-role-id="${role.id}"
                                            title="Cancel">
                                        <span class="material-symbols-outlined">close</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `);

                    // Insert the new row before the creation row
                    $('.creating-role').before($newRow);

                    // Exit creation mode (removes creation row)
                    exitCreationMode();

                    // Show success message
                    addFlashMessage('success', `Role "${role.name}" created successfully!`);
                } else {
                    addFlashMessage('danger', response.message || 'Failed to create role');
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
            $cancelBtn.prop('disabled', false);
            $saveBtn.find('.material-symbols-outlined').text(originalIcon);
        }
    }

    // ========== Event Handlers ==========

    // Edit button click - enter edit mode (only for existing roles)
    $(document).on('click', '.edit-role-btn', function() {
        const roleId = $(this).data('role-id');

        // Skip if this is somehow the creation row
        if (roleId === 'new') {
            return;
        }

        enterEditMode(roleId);
    });

    // Save button click - save changes (only for existing roles)
    $(document).on('click', '.save-role-btn', function() {
        const roleId = $(this).data('role-id');

        // Skip if this is somehow the creation row
        if (roleId === 'new') {
            return;
        }

        saveRoleChanges(roleId);
    });

    // Cancel button click - exit without saving (only for existing roles)
    $(document).on('click', '.cancel-edit-btn', function() {
        const roleId = $(this).data('role-id');

        // Skip if this is somehow the creation row
        if (roleId === 'new') {
            return;
        }

        exitEditMode(roleId);
    });

    // Escape key - cancel edit or creation mode
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            if (isCreatingRole) {
                exitCreationMode();
            } else if (currentlyEditingRowId !== null) {
                exitEditMode(currentlyEditingRowId);
            }
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

    // Enter key in name input - save (only for existing roles, not creation)
    $(document).on('keydown', '.role-name-input', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const $row = $(this).closest('.role-row');
            const roleId = $row.data('role-id');

            // Skip if this is the creation row (handled by separate handler)
            if (roleId === 'new' || $row.hasClass('creating-role')) {
                return;
            }

            saveRoleChanges(roleId);
        }
    });

    // ========== Creation Mode Event Handlers ==========

    // Create button click - enter creation mode
    $(document).on('click', '.add-role-btn', function(e) {
        e.preventDefault();
        enterCreationMode();
    });

    // Save new role button
    $(document).on('click', '.save-new-role-btn', function() {
        saveNewRole();
    });

    // Cancel new role button
    $(document).on('click', '.cancel-new-role-btn', function() {
        exitCreationMode();
    });

    // Live preview updates for new role - name
    $(document).on('input', '.new-role-name', function() {
        const name = $(this).val().trim() || 'Role Name';
        $('.creating-role .role-badge-preview').text(name);
    });

    // Live preview updates for new role - color
    $(document).on('input', '.new-role-color', function() {
        const color = $(this).val();
        $('.creating-role .color-hex').text(color);
        $('.creating-role .role-badge-preview').css('background-color', color);
    });

    // Enter key in new role name input - save
    $(document).on('keydown', '.new-role-name', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveNewRole();
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
