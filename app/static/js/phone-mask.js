function formatPhoneNumber(value) {
    if (!value) return value;

    const phoneNumber = value.replace(/[^\d]/g, '');
    const phoneNumberLength = phoneNumber.length;

    if (phoneNumberLength < 4) return phoneNumber;

    if (phoneNumberLength < 7) {
        return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3)}`;
    }

    return `(${phoneNumber.slice(0, 3)}) ${phoneNumber.slice(3, 6)}-${phoneNumber.slice(6, 10)}`;
}

$(document).ready(function() {
    $('#phone').on('input', function() {
        const formatted = formatPhoneNumber(this.value);
        this.value = formatted;
    });

    $('#phone').on('keydown', function(e) {
        const key = e.key;
        if (key === 'Backspace' || key === 'Delete' || key === 'Tab' || key === 'Escape' || key === 'Enter') {
            return;
        }
        if ((e.ctrlKey || e.metaKey) && (key === 'c' || key === 'v' || key === 'x' || key === 'a')) {
            return;
        }
        if (key >= '0' && key <= '9') {
            return;
        }
        e.preventDefault();
    });
});