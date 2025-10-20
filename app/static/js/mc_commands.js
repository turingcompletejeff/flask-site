/**
 * Minecraft Commands Management JavaScript - Inline Editing (TC-50)
 *
 * Handles inline editing for command management with AJAX updates.
 * Uses jQuery and the global addFlashMessage function from layout.html.
 *
 * Pattern adapted from admin_roles.js for commands with structured args input.
 */

$(function() {
    // ========== State Management ==========
    let currentlyEditingCommandId = null;
    let isCreatingCommand = false;
    const originalCommandData = new Map();

    // ========== Helper Functions ==========

    /**
     * Build options object from args input (space-separated)
     * @param {jQuery} $row - The command row
     * @returns {Object|null} - Options object {"args": ["arg1", "arg2"]} or null
     */
    function buildOptionsObject($row) {
        const argsText = $row.find('.command-args-input').val().trim();

        if (!argsText) {
            return null; // No args
        }

        // Split by spaces, filter empty strings
        const args = argsText.split(/\s+/).filter(arg => arg.length > 0);

        return { args: args };
    }

    /**
     * Update command preview display
     * @param {number} commandId - The command ID
     */
    function updatePreview(commandId) {
        const $row = $(`.command-row[data-command-id="${commandId}"]`);

        const commandName = $row.find('.command-name-input').val().trim() || 'command';
        const argsText = $row.find('.command-args-input').val().trim();

        const previewText = `/${commandName}${argsText ? ' ' + argsText : ''}`;
        $row.find('.command-preview').text(previewText);
    }

    /**
     * Update args display with badges
     * @param {jQuery} $row - The command row
     * @param {Object|null} options - Options object with args array
     */
    function updateArgsDisplay($row, options) {
        const $display = $row.find('.command-args-display');

        if (!options || !options.args || options.args.length === 0) {
            $display.html('<span class="no-args">No arguments</span>');
            return;
        }

        // Create arg badges
        const badgesHtml = options.args.map(arg =>
            `<span class="arg-badge">${escapeHtml(arg)}</span>`
        ).join('');

        $display.html(badgesHtml);
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} - Escaped HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========== Edit Mode Functions ==========

    /**
     * Enter edit mode for a specific command row
     * @param {number} commandId - The command ID
     */
    function enterEditMode(commandId) {
        // Guard: prevent editing during creation
        if (isCreatingCommand) {
            addFlashMessage('warning', 'Please save or cancel the new command before editing another command.');
            return;
        }

        // Prevent editing multiple rows at once
        if (currentlyEditingCommandId !== null) {
            addFlashMessage('warning', 'Please save or cancel the current edit before editing another command.');
            return;
        }

        const $row = $(`.command-row[data-command-id="${commandId}"]`);

        // Store original values
        const originalData = {
            name: $row.find('.command-name-display').text(),
            args: $row.find('.command-args-input').val()
        };
        originalCommandData.set(commandId, originalData);

        // Switch to edit mode
        $row.addClass('editing');

        // Toggle display/input elements
        $row.find('.command-name-display').hide();
        $row.find('.command-name-input').show().focus();

        $row.find('.command-args-display').hide();
        $row.find('.command-args-input').show();

        // Toggle action buttons
        $row.find('.view-mode-actions').hide();
        $row.find('.edit-mode-actions').show();

        // Disable edit/delete buttons in other rows
        $('.command-row').not($row).find('.edit-command-btn, .delete-command-btn').prop('disabled', true);

        // Track current editing row
        currentlyEditingCommandId = commandId;
    }

    /**
     * Exit edit mode
     * @param {number} commandId - The command ID
     * @param {boolean} restoreValues - Whether to restore original values (default: true)
     */
    function exitEditMode(commandId, restoreValues = true) {
        const $row = $(`.command-row[data-command-id="${commandId}"]`);
        const original = originalCommandData.get(commandId);

        if (!original) return;

        // Restore original values only when canceling (not when saving)
        if (restoreValues) {
            $row.find('.command-name-input').val(original.name);
            $row.find('.command-args-input').val(original.args);
            updatePreview(commandId);
        }

        // Clear any error states
        $row.find('.command-name-input, .command-args-input').removeClass('error');

        // Switch back to view mode
        $row.removeClass('editing');

        // Toggle display/input elements
        $row.find('.command-name-display').show();
        $row.find('.command-name-input').hide();

        $row.find('.command-args-display').show();
        $row.find('.command-args-input').hide();

        // Toggle action buttons
        $row.find('.view-mode-actions').show();
        $row.find('.edit-mode-actions').hide();

        // Re-enable edit/delete buttons in other rows
        $('.edit-command-btn, .delete-command-btn').prop('disabled', false);

        // Clear tracking
        currentlyEditingCommandId = null;
        originalCommandData.delete(commandId);
    }

    /**
     * Validate command input fields
     * @param {number} commandId - The command ID
     * @returns {Object} - { valid: boolean, errors: array }
     */
    function validateCommandInput(commandId) {
        const $row = $(`.command-row[data-command-id="${commandId}"]`);
        const errors = [];

        // Get values
        const name = $row.find('.command-name-input').val().trim();

        // Clear previous error states
        $row.find('.command-name-input, .command-args-input').removeClass('error');

        // Validate name (required, max 20 chars)
        if (!name || name.length < 1) {
            errors.push('Command name is required');
            $row.find('.command-name-input').addClass('error');
        } else if (name.length > 20) {
            errors.push('Command name must not exceed 20 characters');
            $row.find('.command-name-input').addClass('error');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Save command changes via AJAX
     * @param {number} commandId - The command ID
     */
    function saveCommandChanges(commandId) {
        // Validate first
        const validation = validateCommandInput(commandId);
        if (!validation.valid) {
            addFlashMessage('danger', validation.errors.join(', '));
            return;
        }

        const $row = $(`.command-row[data-command-id="${commandId}"]`);
        const $saveBtn = $row.find('.save-command-btn');

        // Get new values
        const newData = {
            command_name: $row.find('.command-name-input').val().trim(),
            options: buildOptionsObject($row)
        };

        // Disable save/cancel buttons during request
        $saveBtn.prop('disabled', true);
        $row.find('.cancel-edit-btn').prop('disabled', true);

        // Visual feedback
        const originalIcon = $saveBtn.find('.material-symbols-outlined').text();
        $saveBtn.find('.material-symbols-outlined').text('hourglass_empty');

        $.ajax({
            url: `/mc/commands/${commandId}/update`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newData),
            success: function(response) {
                if (response.status === 'success') {
                    // Update display elements with new values
                    $row.find('.command-name-display').text(newData.command_name);
                    updateArgsDisplay($row, newData.options);

                    // Update preview
                    const argsText = newData.options && newData.options.args ? newData.options.args.join(' ') : '';
                    $row.find('.command-preview').text(`/${newData.command_name}${argsText ? ' ' + argsText : ''}`);

                    // Update input values (for future edits)
                    $row.find('.command-name-input').val(newData.command_name);
                    $row.find('.command-args-input').val(argsText);

                    // Restore button state before exiting edit mode
                    restoreButton();

                    // Exit edit mode (don't restore values - we just saved them)
                    exitEditMode(commandId, false);

                    // Show success message
                    addFlashMessage('success', 'Command updated successfully!');
                } else {
                    addFlashMessage('danger', response.message || 'Failed to update command');
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
     * Enter creation mode - insert new editable command row
     */
    function enterCreationMode() {
        // Guard: prevent multiple creations
        if (isCreatingCommand) {
            addFlashMessage('warning', 'You are already creating a command.');
            return;
        }

        // Guard: prevent creation during edit
        if (currentlyEditingCommandId !== null) {
            addFlashMessage('warning', 'Please save or cancel the current edit before creating a new command.');
            return;
        }

        // Build creation row HTML
        const $creationRow = $(`
            <tr class="command-row creating-command editing" data-command-id="new">
                <td>
                    <input type="text"
                           class="command-name-input new-command-name"
                           placeholder="Enter command name..."
                           maxlength="20">
                </td>
                <td>
                    <input type="text"
                           class="command-args-input new-command-args"
                           placeholder="e.g., player1 100 64 -200">
                </td>
                <td>
                    <code class="command-preview">
                        /<span class="preview-name">command</span> <span class="preview-args"></span>
                    </code>
                </td>
                <td class="actions-cell">
                    <div class="edit-mode-actions">
                        <button type="button"
                                class="btn-icon save-new-command-btn"
                                title="Save">
                            <span class="material-symbols-outlined">check</span>
                        </button>
                        <button type="button"
                                class="btn-icon cancel-new-command-btn"
                                title="Cancel">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                </td>
            </tr>
        `);

        // Insert before the "add-command-row"
        $('.add-command-row').before($creationRow);

        // Hide the "Create New Command" button
        $('.add-command-btn').hide();

        // Disable edit/delete buttons on existing rows
        $('.command-row').not('.creating-command').find('.edit-command-btn, .delete-command-btn').prop('disabled', true);

        // Focus on name input
        $('.new-command-name').focus();

        // Set state flag
        isCreatingCommand = true;
    }

    /**
     * Exit creation mode - remove creation row and restore UI
     */
    function exitCreationMode() {
        // Remove the creation row from DOM
        $('.creating-command').remove();

        // Show the "Create New Command" button
        $('.add-command-btn').show();

        // Re-enable edit/delete buttons on existing rows
        $('.edit-command-btn, .delete-command-btn').prop('disabled', false);

        // Clear state flag
        isCreatingCommand = false;
    }

    /**
     * Validate new command input
     * @returns {Object} - { valid: boolean, errors: array }
     */
    function validateNewCommand() {
        const name = $('.new-command-name').val().trim();
        const errors = [];

        // Clear previous errors
        $('.new-command-name, .new-command-args').removeClass('error');

        // Name validation
        if (!name || name.length < 1) {
            errors.push('Command name is required');
            $('.new-command-name').addClass('error');
        } else if (name.length > 20) {
            errors.push('Command name must not exceed 20 characters');
            $('.new-command-name').addClass('error');
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Save new command via AJAX
     */
    function saveNewCommand() {
        // Validate first
        const validation = validateNewCommand();
        if (!validation.valid) {
            addFlashMessage('danger', validation.errors.join(', '));
            return;
        }

        const $saveBtn = $('.save-new-command-btn');
        const $cancelBtn = $('.cancel-new-command-btn');

        // Get values
        const commandName = $('.new-command-name').val().trim();
        const argsText = $('.new-command-args').val().trim();

        // Build options
        let options = null;
        if (argsText) {
            const args = argsText.split(/\s+/).filter(arg => arg.length > 0);
            options = { args: args };
        }

        const newData = {
            command_name: commandName,
            options: options
        };

        // Disable buttons during request
        $saveBtn.prop('disabled', true);
        $cancelBtn.prop('disabled', true);

        // Visual feedback
        const originalIcon = $saveBtn.find('.material-symbols-outlined').text();
        $saveBtn.find('.material-symbols-outlined').text('hourglass_empty');

        $.ajax({
            url: '/mc/commands/create',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(newData),
            success: function(response) {
                if (response.status === 'success') {
                    // Build new command row HTML with data from server
                    const cmd = response.command;
                    const argsHtml = cmd.options && cmd.options.args
                        ? cmd.options.args.map(arg => `<span class="arg-badge">${escapeHtml(arg)}</span>`).join('')
                        : '<span class="no-args">No arguments</span>';
                    const argsValue = cmd.options && cmd.options.args ? cmd.options.args.join(' ') : '';
                    const previewText = `/${cmd.command_name}${argsValue ? ' ' + argsValue : ''}`;

                    const $newRow = $(`
                        <tr data-command-id="${cmd.command_id}" class="command-row">
                            <td>
                                <strong class="command-name-display">${escapeHtml(cmd.command_name)}</strong>
                                <input type="text"
                                       class="command-name-input"
                                       value="${escapeHtml(cmd.command_name)}"
                                       maxlength="20"
                                       style="display: none;">
                            </td>
                            <td>
                                <div class="command-args-display">
                                    ${argsHtml}
                                </div>
                                <input type="text"
                                       class="command-args-input"
                                       value="${escapeHtml(argsValue)}"
                                       style="display: none;">
                            </td>
                            <td>
                                <code class="command-preview">${escapeHtml(previewText)}</code>
                            </td>
                            <td class="actions-cell">
                                <div class="view-mode-actions">
                                    <button type="button"
                                            class="btn-icon edit-command-btn"
                                            data-command-id="${cmd.command_id}"
                                            title="Edit command">
                                        <span class="material-symbols-outlined">edit</span>
                                    </button>
                                    <button type="button"
                                            class="btn-icon delete-command-btn"
                                            data-command-id="${cmd.command_id}"
                                            data-command-name="${escapeHtml(cmd.command_name)}"
                                            title="Delete command">
                                        <span class="material-symbols-outlined">delete</span>
                                    </button>
                                </div>
                                <div class="edit-mode-actions" style="display: none;">
                                    <button type="button"
                                            class="btn-icon save-command-btn"
                                            data-command-id="${cmd.command_id}"
                                            title="Save">
                                        <span class="material-symbols-outlined">check</span>
                                    </button>
                                    <button type="button"
                                            class="btn-icon cancel-edit-btn"
                                            data-command-id="${cmd.command_id}"
                                            title="Cancel">
                                        <span class="material-symbols-outlined">close</span>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `);

                    // Insert the new row before the creation row
                    $('.creating-command').before($newRow);

                    // Exit creation mode (removes creation row)
                    exitCreationMode();

                    // Show success message
                    addFlashMessage('success', `Command "${cmd.command_name}" created successfully!`);
                } else {
                    addFlashMessage('danger', response.message || 'Failed to create command');
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

    // Edit button click - enter edit mode
    $(document).on('click', '.edit-command-btn', function() {
        const commandId = $(this).data('command-id');
        if (commandId === 'new') return; // Safety check
        enterEditMode(commandId);
    });

    // Save button click - save changes
    $(document).on('click', '.save-command-btn', function() {
        const commandId = $(this).data('command-id');
        if (commandId === 'new') return;
        saveCommandChanges(commandId);
    });

    // Cancel button click - exit without saving
    $(document).on('click', '.cancel-edit-btn', function() {
        const commandId = $(this).data('command-id');
        if (commandId === 'new') return;
        exitEditMode(commandId);
    });

    // Escape key - cancel edit or creation mode
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            if (isCreatingCommand) {
                exitCreationMode();
            } else if (currentlyEditingCommandId !== null) {
                exitEditMode(currentlyEditingCommandId);
            }
        }
    });

    // Live preview updates during edit - name
    $(document).on('input', '.command-name-input:not(.new-command-name)', function() {
        const commandId = $(this).closest('.command-row').data('command-id');
        if (commandId !== 'new') {
            updatePreview(commandId);
        }
    });

    // Live preview updates during edit - args
    $(document).on('input', '.command-args-input:not(.new-command-args)', function() {
        const commandId = $(this).closest('.command-row').data('command-id');
        if (commandId !== 'new') {
            updatePreview(commandId);
        }
    });

    // Enter key in name input - save
    $(document).on('keydown', '.command-name-input:not(.new-command-name)', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const commandId = $(this).closest('.command-row').data('command-id');
            if (commandId !== 'new') {
                saveCommandChanges(commandId);
            }
        }
    });

    // ========== Creation Mode Event Handlers ==========

    // Create button click - enter creation mode
    $(document).on('click', '.add-command-btn', function(e) {
        e.preventDefault();
        enterCreationMode();
    });

    // Save new command button
    $(document).on('click', '.save-new-command-btn', function() {
        saveNewCommand();
    });

    // Cancel new command button
    $(document).on('click', '.cancel-new-command-btn', function() {
        exitCreationMode();
    });

    // Live preview for new command - name
    $(document).on('input', '.new-command-name', function() {
        const name = $(this).val().trim() || 'command';
        $('.creating-command .preview-name').text(name);
    });

    // Live preview for new command - args
    $(document).on('input', '.new-command-args', function() {
        const args = $(this).val().trim();
        $('.creating-command .preview-args').text(args);
    });

    // Enter key in new command name
    $(document).on('keydown', '.new-command-name', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveNewCommand();
        }
    });

    // ========== Delete Command Modal Handling ==========

    const $deleteModal = $('#deleteCommandModal');
    const $deleteForm = $('#deleteCommandForm');
    const $deleteMessage = $('#deleteCommandMessage');

    // Handle delete button clicks
    $(document).on('click', '.delete-command-btn', function() {
        const commandId = $(this).data('command-id');
        const commandName = $(this).data('command-name');

        // Set the form action to the delete URL
        $deleteForm.attr('action', `/mc/commands/${commandId}/delete`);

        // Set the confirmation message
        $deleteMessage.html(
            `Are you sure you want to delete the command "<strong>${escapeHtml(commandName)}</strong>"?<br><br>` +
            `This action cannot be undone.`
        );

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
