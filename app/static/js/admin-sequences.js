/**
 * Admin Sequence Fix - jQuery UI Dialog Implementation
 * TC-61: Enhanced sequence fix with progress tracking
 */

$(function() {
    // Initialize dialogs and bind events on DOM ready
    initializeDialogs();

    // Bind button click event
    $('#fixSequencesBtn').on('click', showConfirmationDialog);
});

// Flag to prevent concurrent operations
let sequenceOperationInProgress = false;

// Table order for sequential processing
const TABLE_ORDER = ['blog-posts', 'users', 'roles', 'minecraft'];

/**
 * Initialize all jQuery UI dialogs
 */
function initializeDialogs() {
    // Confirmation Dialog
    $("#sequenceConfirmDialog").dialog({
        autoOpen: false,
        modal: true,
        resizable: false,
        draggable: false,
        width: 500,
        title: "Confirm Sequence Synchronization",
        buttons: [
            {
                text: "Cancel",
                class: "btn-secondary",
                click: function() {
                    $(this).dialog("close");
                }
            },
            {
                text: "Synchronize Sequences",
                class: "btn-primary",
                click: function() {
                    $(this).dialog("close");
                    executeSequenceFix();
                }
            }
        ]
    });

    // Progress Dialog
    $("#sequenceProgressDialog").dialog({
        autoOpen: false,
        modal: true,
        resizable: false,
        draggable: false,
        closeOnEscape: false,
        width: 500,
        title: "Synchronizing Sequences...",
        open: function() {
            // Remove close button from title bar
            $(this).parent().find(".ui-dialog-titlebar-close").hide();
        }
    });

    // Initialize progress bar
    $("#sequenceProgressBar").progressbar({
        value: 0,
        max: 100
    });

    // Results Dialog (buttons set dynamically based on success/error)
    $("#sequenceResultsDialog").dialog({
        autoOpen: false,
        modal: true,
        resizable: false,
        draggable: false,
        width: 550
    });
}

/**
 * Show confirmation dialog
 */
function showConfirmationDialog() {
    // Prevent multiple simultaneous operations
    if (sequenceOperationInProgress) {
        console.warn('Sequence operation already in progress');
        return;
    }

    $("#sequenceConfirmDialog").dialog("open");
}

/**
 * Execute sequence fix with sequential AJAX calls
 */
async function executeSequenceFix() {
    sequenceOperationInProgress = true;

    // Show progress modal
    $("#sequenceProgressDialog").dialog("open");
    $("#sequenceProgressBar").progressbar("value", 0);
    $(".sequence-current-table").text("Initializing...");

    const results = [];
    const progressIncrement = 100 / TABLE_ORDER.length; // 25% per table

    try {
        // Process each table sequentially
        for (let i = 0; i < TABLE_ORDER.length; i++) {
            const tableName = TABLE_ORDER[i];
            const tableDisplayName = getTableDisplayName(tableName);

            // Update progress text
            $(".sequence-current-table").text(`Processing: ${tableDisplayName}`);

            try {
                // Make AJAX call for this table
                const result = await fixSingleTableSequence(tableName);
                results.push(result);

                // Update progress bar
                const progress = (i + 1) * progressIncrement;
                $("#sequenceProgressBar").progressbar("value", progress);

            } catch (error) {
                // Log error but continue with other tables
                console.error(`Error fixing ${tableName}:`, error);
                results.push({
                    status: 'error',
                    table: tableName,
                    message: error.message || 'Network error occurred'
                });

                // Update progress bar even on error
                const progress = (i + 1) * progressIncrement;
                $("#sequenceProgressBar").progressbar("value", progress);
            }

            // Small delay between requests to avoid overwhelming server
            if (i < TABLE_ORDER.length - 1) {
                await sleep(100);
            }
        }

        // All tables processed, show results
        $("#sequenceProgressDialog").dialog("close");
        showResults(results);

    } catch (error) {
        // Unexpected error in the loop
        console.error('Unexpected error in executeSequenceFix:', error);
        $("#sequenceProgressDialog").dialog("close");
        showErrorResults({
            message: 'An unexpected error occurred during synchronization'
        });
    } finally {
        sequenceOperationInProgress = false;
    }
}

/**
 * Fix sequence for a single table via AJAX
 * @param {string} tableName - URL-friendly table name
 * @returns {Promise<object>} - Result object
 */
function fixSingleTableSequence(tableName) {
    return new Promise((resolve, reject) => {
        $.ajax({
            url: `/admin/sequences/${tableName}`,
            method: 'POST',
            contentType: 'application/json',
            timeout: 10000, // 10 second timeout per table
            success: function(data) {
                resolve(data);
            },
            error: function(xhr, status, error) {
                let errorMsg = 'Network error occurred';

                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                } else if (status === 'timeout') {
                    errorMsg = 'Request timed out';
                }

                reject({
                    status: 'error',
                    table: tableName,
                    message: errorMsg
                });
            }
        });
    });
}

/**
 * Show results dialog based on aggregated results
 * @param {Array<object>} results - Array of result objects
 */
function showResults(results) {
    const successCount = results.filter(r => r.status === 'success').length;
    const failedCount = results.filter(r => r.status === 'error').length;
    const totalCount = results.length;

    if (failedCount === 0) {
        // All successful
        showSuccessResults(results);
    } else if (successCount === 0) {
        // All failed
        showAllErrorResults(results);
    } else {
        // Partial success
        showPartialResults(results, successCount, failedCount);
    }
}

/**
 * Show success results (all tables fixed)
 * @param {Array<object>} results - Result objects
 */
function showSuccessResults(results) {
    let html = '<div class="sequence-success">';
    html += '<p class="success-message">';
    html += '<span class="success-icon">✅</span>';
    html += 'All database sequences synchronized successfully!';
    html += '</p>';

    html += '<h4 class="sequence-results-title">Results:</h4>';
    html += '<ul class="sequence-results-list">';

    results.forEach(function(result) {
        const displayName = getTableDisplayName(result.table);
        html += `<li class="success">`;
        html += `<span class="table-name">${displayName}</span>`;
        html += `<span class="table-result">Next ID: ${result.new_value}</span>`;
        html += `</li>`;
    });

    html += '</ul></div>';

    $("#sequenceResultsContent").html(html);
    $("#sequenceResultsDialog").dialog("option", "title", "✅ Sequences Synchronized");
    $("#sequenceResultsDialog").dialog("option", "buttons", [
        {
            text: "Done",
            class: "btn-success",
            click: function() {
                $(this).dialog("close");
                if (typeof addFlashMessage === 'function') {
                    addFlashMessage('success', 'Database sequences synchronized successfully');
                }
            }
        }
    ]);
    $("#sequenceResultsDialog").dialog("open");
}

/**
 * Show error results (all tables failed)
 * @param {Array<object>} results - Result objects
 */
function showAllErrorResults(results) {
    let html = '<div class="sequence-error">';
    html += '<p class="error-message">';
    html += '<span class="error-icon">❌</span>';
    html += 'Failed to synchronize sequences';
    html += '</p>';

    html += '<h4 class="sequence-results-title">Errors:</h4>';
    html += '<ul class="sequence-results-list">';

    results.forEach(function(result) {
        const displayName = getTableDisplayName(result.table);
        html += `<li class="error">`;
        html += `<span class="table-name">${displayName}</span>`;
        html += `<span class="table-result">${result.message}</span>`;
        html += `</li>`;
    });

    html += '</ul></div>';

    $("#sequenceResultsContent").html(html);
    $("#sequenceResultsDialog").dialog("option", "title", "❌ Synchronization Failed");
    $("#sequenceResultsDialog").dialog("option", "buttons", [
        {
            text: "Close",
            class: "btn-danger",
            click: function() {
                $(this).dialog("close");
                if (typeof addFlashMessage === 'function') {
                    addFlashMessage('danger', 'Failed to synchronize sequences');
                }
            }
        }
    ]);
    $("#sequenceResultsDialog").dialog("open");
}

/**
 * Show partial results (some success, some failure)
 * @param {Array<object>} results - Result objects
 * @param {number} successCount - Number of successful operations
 * @param {number} failedCount - Number of failed operations
 */
function showPartialResults(results, successCount, failedCount) {
    let html = '<div class="sequence-partial">';
    html += '<p class="error-message">';
    html += '<span class="error-icon">⚠️</span>';
    html += `Partial Success: ${successCount} of ${results.length} sequences fixed`;
    html += '</p>';

    html += '<h4 class="sequence-results-title">Results:</h4>';
    html += '<ul class="sequence-results-list">';

    results.forEach(function(result) {
        const displayName = getTableDisplayName(result.table);
        const isSuccess = result.status === 'success';

        html += `<li class="${isSuccess ? 'success' : 'error'}">`;
        html += `<span class="table-name">${displayName}</span>`;

        if (isSuccess) {
            html += `<span class="table-result">✓ Next ID: ${result.new_value}</span>`;
        } else {
            html += `<span class="table-result">✗ ${result.message}</span>`;
        }

        html += `</li>`;
    });

    html += '</ul>';

    // Add summary
    html += '<div class="sequence-summary">';
    html += '<div class="sequence-summary-item">';
    html += '<span class="label">Successful:</span>';
    html += `<span class="value">${successCount}</span>`;
    html += '</div>';
    html += '<div class="sequence-summary-item">';
    html += '<span class="label">Failed:</span>';
    html += `<span class="value">${failedCount}</span>`;
    html += '</div>';
    html += '</div>';

    html += '</div>';

    $("#sequenceResultsContent").html(html);
    $("#sequenceResultsDialog").dialog("option", "title", "⚠️ Partial Success");
    $("#sequenceResultsDialog").dialog("option", "buttons", [
        {
            text: "Close",
            class: "btn-secondary",
            click: function() {
                $(this).dialog("close");
                if (typeof addFlashMessage === 'function') {
                    addFlashMessage('warning', `${successCount} of ${results.length} sequences synchronized`);
                }
            }
        }
    ]);
    $("#sequenceResultsDialog").dialog("open");
}

/**
 * Show generic error results
 * @param {object} error - Error object
 */
function showErrorResults(error) {
    let html = '<div class="sequence-error">';
    html += '<p class="error-message">';
    html += '<span class="error-icon">❌</span>';
    html += 'An error occurred while synchronizing sequences';
    html += '</p>';
    html += `<div class="error-details">${error.message}</div>`;
    html += '</div>';

    $("#sequenceResultsContent").html(html);
    $("#sequenceResultsDialog").dialog("option", "title", "❌ Error");
    $("#sequenceResultsDialog").dialog("option", "buttons", [
        {
            text: "Close",
            class: "btn-danger",
            click: function() {
                $(this).dialog("close");
                if (typeof addFlashMessage === 'function') {
                    addFlashMessage('danger', 'Failed to synchronize sequences');
                }
            }
        }
    ]);
    $("#sequenceResultsDialog").dialog("open");
}

/**
 * Get human-readable display name for a table
 * @param {string} tableName - URL-friendly or database table name
 * @returns {string} - Display name
 */
function getTableDisplayName(tableName) {
    const displayNames = {
        'blog-posts': 'Blog Posts',
        'blog_posts': 'Blog Posts',
        'users': 'Users',
        'roles': 'Roles',
        'minecraft': 'Minecraft Commands',
        'minecraft_commands': 'Minecraft Commands'
    };

    return displayNames[tableName] || tableName;
}

/**
 * Sleep utility function
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Warn user before leaving page during operation
 */
$(window).on('beforeunload', function(e) {
    if (sequenceOperationInProgress) {
        const message = 'Sequence synchronization in progress. Are you sure you want to leave?';
        e.returnValue = message; // Standard way
        return message; // For some browsers
    }
});
