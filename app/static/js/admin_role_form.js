// Sync color picker with hex input and preview badge
$(document).ready(function() {
    const $colorPicker = $('#badge_color_picker');
    const $colorHex = $('#badge_color_hex');
    const $preview = $('#badge_preview');

    if ($colorPicker.length && $colorHex.length && $preview.length) {
        // Update preview when color picker changes
        $colorPicker.on('input', function() {
            const color = $(this).val();
            $colorHex.val(color);
            $preview.css('background-color', color);
        });

        // Initialize preview with current color value
        const currentColor = $colorPicker.val();
        $colorHex.val(currentColor);
        $preview.css('background-color', currentColor);
    }
});
