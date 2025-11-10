/**
 * Minecraft Server Status Indicator
 * Handles server status polling, display updates, and command validation
 */

// Global variables
var ansi_esc = new RegExp(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/, "g");
var commandList = [];
var prevCommand = "";

// Status polling configuration
var statusPollInterval = null;
var lastStatusCheck = null;
var isRefreshing = false;
var lastRefreshTime = 0;
const POLL_INTERVAL_MS = 900000; // 15 minutes
const DEBOUNCE_MS = 1000; // 1 second debounce for manual refresh
const STATUS_CACHE_DURATION_MS = 3600000; // 1 hour
const STORAGE_KEY = 'mc_server_status';

/**
 * Format timestamp as relative time (e.g., "2 minutes ago")
 */
function formatRelativeTime(timestamp) {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);

  if (diffSec < 60) {
    return 'Just now';
  } else if (diffMin < 60) {
    return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} hour${diffHour !== 1 ? 's' : ''} ago`;
  } else {
    return then.toLocaleString();
  }
}

/**
 * Update status timestamp display
 */
function updateTimestamp() {
  if (lastStatusCheck) {
    $('#status-timestamp').text('Last checked: ' + formatRelativeTime(lastStatusCheck));
  }
}

/**
 * Load status from localStorage
 */
function loadCachedStatus() {
  try {
    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached) {
      const data = JSON.parse(cached);
      const cacheAge = new Date() - new Date(data.timestamp);

      // Only use cache if less than 1 hour old
      if (cacheAge < STATUS_CACHE_DURATION_MS) {
        updateStatusDisplay(data.status, data.timestamp);
        return true;
      } else {
        // Clear old cache
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  } catch (e) {
    console.warn('Failed to load cached status:', e);
  }
  return false;
}

/**
 * Save status to localStorage
 */
function saveStatusToCache(status, timestamp) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      status: status,
      timestamp: timestamp
    }));
  } catch (e) {
    console.warn('Failed to save status to cache:', e);
  }
}

/**
 * Update status indicator and text
 */
function updateStatusDisplay(status, timestamp) {
  const indicator = $('#status-indicator');
  const statusText = $('#status-text');

  // Remove all status classes
  indicator.removeClass('online offline unknown loading');

  // Update based on status
  switch(status) {
    case 'online':
      indicator.addClass('online');
      statusText.text('Server Online');
      statusText.css('color', '#4CAF50');
      enableCommandInput();
      hideOfflineMessage();
      break;
    case 'offline':
      indicator.addClass('offline');
      statusText.text('Server Offline');
      statusText.css('color', '#F44336');
      disableCommandInput();
      showOfflineMessage();
      break;
    case 'unknown':
    default:
      indicator.addClass('unknown');
      statusText.text('Status Unknown');
      statusText.css('color', '#757575');
      disableCommandInput();
      hideOfflineMessage();
      break;
  }

  // Update timestamp
  lastStatusCheck = timestamp;
  updateTimestamp();

  // Save to cache
  saveStatusToCache(status, timestamp);
}

/**
 * Show offline message
 */
function showOfflineMessage() {
  $('#offline-message').addClass('show');
}

/**
 * Hide offline message
 */
function hideOfflineMessage() {
  $('#offline-message').removeClass('show');
}

/**
 * Disable command input when server is offline
 */
function disableCommandInput() {
  $('#terminal-wrapper').addClass('disabled');
  $('#mc-input').prop('disabled', true);
  $('#mc-cmd').prop('disabled', true);
}

/**
 * Enable command input when server is online
 */
function enableCommandInput() {
  $('#terminal-wrapper').removeClass('disabled');
  $('#mc-input').prop('disabled', false);
  $('#mc-cmd').prop('disabled', false);
}

/**
 * Check server status via /mc/status endpoint
 * Note: Requires MC_ENDPOINTS.status to be defined in template
 */
function checkServerStatus() {
  // Prevent concurrent requests
  if (isRefreshing) {
    return;
  }

  isRefreshing = true;

  // Show loading state
  const indicator = $('#status-indicator');
  const refreshButton = $('#refresh-button');

  indicator.removeClass('online offline unknown').addClass('loading');
  refreshButton.addClass('refreshing').prop('disabled', true);
  $('#status-text').text('Checking status...').css('color', 'var(--text)');

  $.ajax({
    url: MC_ENDPOINTS.status,
    method: "GET",
    timeout: 5000 // 5 second timeout (backend should respond in ~2 seconds)
  }).done(function(data) {
    // Update display with server status
    const status = data.status || 'unknown';
    const timestamp = data.timestamp || new Date().toISOString();

    updateStatusDisplay(status, timestamp);

    // If online, also update player list from status data
    if (status === 'online' && data.players) {
      updatePlayerList(data);
    } else {
      // Clear player list if not online
      $('#rcon-query-players').empty();
      if (status === 'offline') {
        $('#rcon-query-players').text('Server offline');
      } else {
        $('#rcon-query-players').text('Status unavailable');
      }
    }

  }).fail(function(xhr, textStatus, error) {
    console.error('Status check failed:', textStatus, error);

    // Show offline status on timeout/error (treat as offline)
    updateStatusDisplay('offline', new Date().toISOString());

    // Log error but don't spam user with flash messages on automatic polls
    if (textStatus === 'timeout') {
      console.warn('Status check timed out - treating as offline');
    }

  }).always(function() {
    // Remove loading state
    isRefreshing = false;
    $('#refresh-button').removeClass('refreshing').prop('disabled', false);
    lastRefreshTime = Date.now();
  });
}

/**
 * Update player list from status data
 */
function updatePlayerList(data) {
  if (!data.players) return;

  $('#rcon-query-players').empty();

  const onlinePlayers = parseInt(data.players.online) || 0;
  const maxPlayers = parseInt(data.players.max) || 0;
  const playerList = data.players.list || [];

  // Check both player count and array length to handle edge cases
  if (onlinePlayers === 0 || playerList.length === 0) {
    $('#rcon-query-players').text('No players connected.');
  } else {
    playerList.forEach(function(playerName) {
      let cleanName = playerName.replace(ansi_esc, '');
      let thisRow = $('<tr>');
      let nameCell = $('<td>').text(cleanName);

      let kickButton = $('<button>')
        .addClass('rcon-kick')
        .text('K')
        .data('playerName', cleanName);
      let actionCell = $('<td>').append(kickButton);

      thisRow.append(nameCell);
      thisRow.append(actionCell);
      $('#rcon-query-players').append(thisRow);
    });
  }

  // Update MOTD if available
  if (data.motd) {
    $('#rcon-motd').text(data.motd.replace(ansi_esc, ''));
  }

  // Update version if available
  if (data.version) {
    $('#rcon-version').text(data.version);
  }

  // Update map if available
  if (data.map) {
    $('#rcon-map').text(data.map);
  }

  // Update plugins if available
  if (data.plugins) {
    $('#rcon-plugins').text(data.plugins);
  }
}

/**
 * Start polling for status updates
 */
function startStatusPolling() {
  // Check immediately on start
  checkServerStatus();

  // Set up interval for periodic checks
  if (statusPollInterval) {
    clearInterval(statusPollInterval);
  }

  statusPollInterval = setInterval(function() {
    // Only poll if page is visible
    if (!document.hidden) {
      checkServerStatus();
    }
  }, POLL_INTERVAL_MS);
}

/**
 * Stop polling for status updates
 */
function stopStatusPolling() {
  if (statusPollInterval) {
    clearInterval(statusPollInterval);
    statusPollInterval = null;
  }
}

/**
 * Handle manual refresh button click
 */
function handleRefreshClick() {
  const now = Date.now();
  const timeSinceLastRefresh = now - lastRefreshTime;

  // Debounce rapid clicks (minimum 1 second between requests)
  if (timeSinceLastRefresh < DEBOUNCE_MS) {
    addFlashMessage('info', 'Please wait before refreshing again.');
    return;
  }

  checkServerStatus();
}

/**
 * Handle Page Visibility API changes
 */
function handleVisibilityChange() {
  if (document.hidden) {
    // Page is hidden - stop polling to save resources
    stopStatusPolling();
  } else {
    // Page is visible - resume polling
    startStatusPolling();
  }
}

function getCommandList() {
  $.get(MC_ENDPOINTS.list)
    .done(function(data) {
      commandList = data;
    }).fail(function(err) {
      console.warn("RCON init failed: ", err);
    });
}

function runBaseRconQuery() {
  $.get(MC_ENDPOINTS.query)
    .done(function(response) {
      // Handle response structure: { status: 'success', data: {...} }
      const data = response.data || response;

      // show motd (with fallback)
      if (data.motd) {
        $("#rcon-motd").text(data.motd.replace(ansi_esc,''));
      }
      // map (with fallback)
      if (data.map) {
        $("#rcon-map").text(data.map);
      }
      // plugins and version (with fallbacks)
      if (data.plugins) {
        $("#rcon-plugins").text(data.plugins);
      }
      if (data.version) {
        $("#rcon-version").text(data.version);
      }

      // build players list
      $("#rcon-query-players").empty();
      const numPlayers = parseInt(data.numplayers) || 0;
      const players = data.players || [];

      if (numPlayers === 0 || players.length === 0) {
        $("#rcon-query-players").text("No players connected.");
      } else {
        players.forEach(function(player) {
          let thisRow = $("<tr>");
          // create a row that will display the player's name
          let playerName = player.replace(ansi_esc,'');
          let nameCell = $("<td>").text(playerName);

          let kickButton = $("<button>").addClass("rcon-kick").text("K").data("playerName",playerName);
          let actionCell = $("<td>").append(kickButton);

          thisRow.append(nameCell);
          thisRow.append(actionCell);
          // append it to the players list
          $("#rcon-query-players").append(thisRow);
        });
      }
    }).fail(function(err) {
      console.warn("RCON query failed: ", err);
    });
}

function rconCommand() {
  let cmd = $("#mc-input").val();

  // Check if server is online before sending command
  const indicator = $('#status-indicator');
  if (!indicator.hasClass('online')) {
    addFlashMessage('warning', 'Cannot send command: Server is not online.');
    return;
  }

  $.post(MC_ENDPOINTS.command,
    {
      "command": cmd
    }
  ).done(function(data) {
    $("#rcon-response").text(data.replace(ansi_esc,''));
    $("#mc-input").attr("placeholder",cmd);
    $("#mc-input").val("");
    prevCommand = cmd;
  }).fail(function (err) {
    console.warn("RCON Command failed: ",err);
    addFlashMessage('danger', 'Command failed. Please check server status.');
  });
}

function kickPlayer(playerName) {
  // Check if server is online before kicking
  const indicator = $('#status-indicator');
  if (!indicator.hasClass('online')) {
    addFlashMessage('warning', 'Cannot kick player: Server is not online.');
    return;
  }

  $.post(MC_ENDPOINTS.command,
    {
      "command": "/kick " + playerName
    }
  ).done(function(data) {
    // display player kicked message
    $("#rcon-response").text(data.replace(ansi_esc,''));
    // remove from list
    $("button.rcon-kick").parents("tr").remove();
    // if 0 players left, print "no players"
    if($("#rcon-query-players tr").length === 0) {
      $("#rcon-query-players").text("No players connected.");
    }
  }).fail(function (err) {
    console.warn("RCON Command failed: ",err);
    addFlashMessage('danger', 'Kick command failed. Please check server status.');
  });
}

/* Initialize on document ready */
$(document).ready(function() {
  getCommandList();

  // Load cached status immediately (before first API call)
  const hasCachedStatus = loadCachedStatus();

  // Start status polling
  startStatusPolling();

  // Set up Page Visibility API listener
  document.addEventListener('visibilitychange', handleVisibilityChange);

  // Update timestamp display every 30 seconds
  setInterval(updateTimestamp, 30000);

  // Manual refresh button click handler
  $('#refresh-button').on('click', handleRefreshClick);

  // Note: Player list populated by checkServerStatus() - no need for separate query

  $("#mc-input").on("keyup",function(e) {
    if(e.which === 13) { // on enter key up
      e.preventDefault();
      rconCommand(); // call command fn as if user pressed send
    }
  });

  $("#mc-input").keydown(function(e) {
    if (e.keyCode === 38) { // on up^^ key
      e.preventDefault();
      $("#mc-input").val(prevCommand);
    }
  });

  $("#rcon-query-players").on("click", "button.rcon-kick",function(e) {
    e.preventDefault();
    kickPlayer($(this).data("playerName"));
  });

  // Clean up on page unload
  $(window).on('beforeunload', function() {
    stopStatusPolling();
  });
});
