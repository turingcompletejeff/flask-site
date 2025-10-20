/**
 * Admin Roles Management JavaScript
 *
 * Handles color picker interactions and AJAX updates for role badge colors.
 * Uses jQuery and the global addFlashMessage function from layout.html.
 */

$(function() {
    const $colorPickers = $('.role-color-picker');

    $colorPickers.each(function() {
        const $picker = $(this);
        const roleId = $picker.data('role-id');
        const originalColor = $picker.data('original-color');
        const $hexDisplay = $(`#hex-${roleId}`);
        const $preview = $(`#preview-${roleId}`);
        const $saveBtn = $(`#save-${roleId}`);
        const $resetBtn = $(`#reset-${roleId}`);

        // Update preview and hex display as user changes color
        $picker.on('input', function() {
            const newColor = $(this).val();
            $hexDisplay.text(newColor);
            $preview.css('background-color', newColor);

            // Show save/reset buttons if color changed
            if (newColor !== originalColor) {
                $saveBtn.show();
                $resetBtn.show();
            } else {
                $saveBtn.hide();
                $resetBtn.hide();
            }
        });

        // Save color via AJAX
        $saveBtn.on('click', function() {
            const newColor = $picker.val();

            // Disable buttons during request
            $saveBtn.prop('disabled', true);
            $resetBtn.prop('disabled', true);
            $saveBtn.text('Saving...');

            $.ajax({
                url: $saveBtn.data('update-url') || '/admin/update_role_badge',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    role_id: parseInt(roleId),
                    badge_color: newColor
                }),
                success: function(data) {
                    if (data.status === 'success') {
                        // Update original color
                        $picker.data('original-color', newColor);

                        // Hide buttons
                        $saveBtn.hide();
                        $resetBtn.hide();

                        // Show success message using global function from layout.html
                        addFlashMessage('success', 'Badge color updated successfully!');
                    } else {
                        addFlashMessage('danger', data.message || 'Failed to update badge color');
                        // Reset to original
                        resetToOriginal();
                    }
                },
                error: function(xhr) {
                    let errorMsg = 'Network error occurred';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        errorMsg = xhr.responseJSON.message;
                    }
                    addFlashMessage('danger', errorMsg);
                    // Reset to original
                    resetToOriginal();
                },
                complete: function() {
                    $saveBtn.prop('disabled', false);
                    $resetBtn.prop('disabled', false);
                    $saveBtn.text('Save Color');
                }
            });
        });

        // Reset to original color
        $resetBtn.on('click', function() {
            resetToOriginal();
        });

        // Helper function to reset color picker
        function resetToOriginal() {
            $picker.val(originalColor);
            $hexDisplay.text(originalColor);
            $preview.css('background-color', originalColor);
            $saveBtn.hide();
            $resetBtn.hide();
        }
    });

    // Delete role confirmation modal handling
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
