// Ana JavaScript dosyası
document.addEventListener('DOMContentLoaded', function() {
    // Flash mesajlarını otomatik gizle
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });
});
