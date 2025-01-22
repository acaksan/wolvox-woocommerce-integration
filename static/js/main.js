// Dashboard istatistiklerini güncelle
async function updateDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) throw new Error('İstatistikler alınamadı');
        
        const data = await response.json();
        if (!data.success) throw new Error(data.message);
        
        document.getElementById('total-products').textContent = data.total_products;
        document.getElementById('synced-products').textContent = data.synced_products;
        document.getElementById('stock-updates').textContent = data.stock_updates;
        document.getElementById('price-updates').textContent = data.price_updates;
        
    } catch (error) {
        console.error('İstatistikler alınamadı:', error);
        showToast('error', 'İstatistikler alınamadı: ' + error.message);
    }
}

// Son aktiviteleri güncelle
async function updateRecentActivities() {
    try {
        const response = await fetch('/api/dashboard/activities');
        if (!response.ok) throw new Error('Son işlemler alınamadı');
        
        const data = await response.json();
        if (!data.success) throw new Error(data.message);
        
        const tbody = document.getElementById('recent-activities');
        tbody.innerHTML = '';
        
        data.activities.forEach(activity => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${activity.date}</td>
                <td>${activity.type}</td>
                <td>
                    <span class="badge bg-${activity.status === 'BAŞARILI' ? 'success' : 'warning'}">
                        ${activity.status}
                    </span>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Son işlemler getirilirken hata:', error);
        showToast('error', 'Son işlemler alınamadı: ' + error.message);
    }
}

// Hataları güncelle
async function updateErrors() {
    try {
        const response = await fetch('/api/dashboard/errors');
        if (!response.ok) throw new Error('Hatalar alınamadı');
        
        const data = await response.json();
        if (!data.success) throw new Error(data.message);
        
        const tbody = document.getElementById('errors-list');
        tbody.innerHTML = '';
        
        data.errors.forEach(error => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${error.date}</td>
                <td>
                    <span class="badge bg-${error.type === 'UYARI' ? 'warning' : 'danger'}">
                        ${error.type}
                    </span>
                </td>
                <td>${error.message}</td>
            `;
            tbody.appendChild(tr);
        });
        
    } catch (error) {
        console.error('Hatalar alınamadı:', error);
        showToast('error', 'Hatalar alınamadı: ' + error.message);
    }
}

// Tarih formatla
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Toast bildirimi göster
function showToast(type, message) {
    const toastContainer = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : 'success'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // 5 saniye sonra toast'ı kaldır
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Dashboard'ı güncelle
async function updateDashboard() {
    await updateDashboardStats();
    await updateRecentActivities();
    await updateErrors();
}

// Ürün senkronizasyonu
function syncProduct(stokKodu) {
    return fetch(`/api/sync/product/${stokKodu}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showToast('success', 'Başarılı', result.message);
            } else {
                showToast('error', 'Hata', result.message);
            }
            return result;
        })
        .catch(error => {
            console.error('Ürün senkronizasyon hatası:', error);
            showToast('error', 'Hata', 'Ürün senkronize edilirken bir hata oluştu');
            throw error;
        });
}

// Toplu senkronizasyon
function syncAllProducts() {
    showToast('info', 'Bilgi', 'Toplu senkronizasyon başlatıldı...');
    
    return fetch('/api/sync/all', { method: 'POST' })
        .then(response => response.json())
        .then(results => {
            const successful = results.filter(r => r.success).length;
            const failed = results.filter(r => !r.success).length;
            
            showToast('success', 'Başarılı', 
                `Toplu senkronizasyon tamamlandı. ${successful} başarılı, ${failed} başarısız`);
            
            // Dashboard'ı güncelle
            updateDashboard();
            return results;
        })
        .catch(error => {
            console.error('Toplu senkronizasyon hatası:', error);
            showToast('error', 'Hata', 'Toplu senkronizasyon sırasında bir hata oluştu');
            throw error;
        });
}

// Stok senkronizasyonu
function syncStock(stokKodu) {
    return fetch(`/api/sync/stock/${stokKodu}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showToast('success', 'Başarılı', result.message);
            } else {
                showToast('error', 'Hata', result.message);
            }
            return result;
        })
        .catch(error => {
            console.error('Stok senkronizasyon hatası:', error);
            showToast('error', 'Hata', 'Stok senkronize edilirken bir hata oluştu');
            throw error;
        });
}

// Fiyat senkronizasyonu
function syncPrice(stokKodu) {
    return fetch(`/api/sync/price/${stokKodu}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showToast('success', 'Başarılı', result.message);
            } else {
                showToast('error', 'Hata', result.message);
            }
            return result;
        })
        .catch(error => {
            console.error('Fiyat senkronizasyon hatası:', error);
            showToast('error', 'Hata', 'Fiyat senkronize edilirken bir hata oluştu');
            throw error;
        });
}

// Sayfa yüklendiğinde
document.addEventListener('DOMContentLoaded', () => {
    // İlk yükleme
    updateDashboard();
    
    // Her 30 saniyede bir güncelle
    setInterval(updateDashboard, 30000);
    
    // Toast container'ı oluştur
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Toplu senkronizasyon butonu
    const syncAllButton = document.getElementById('sync-all-button');
    if (syncAllButton) {
        syncAllButton.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Senkronize ediliyor...';
            
            syncAllProducts()
                .finally(() => {
                    this.disabled = false;
                    this.textContent = 'Tümünü Senkronize Et';
                });
        });
    }
    
    // Ürün senkronizasyon butonları
    document.querySelectorAll('[data-sync-product]').forEach(button => {
        button.addEventListener('click', function() {
            const stokKodu = this.dataset.syncProduct;
            this.disabled = true;
            
            syncProduct(stokKodu)
                .finally(() => {
                    this.disabled = false;
                });
        });
    });
    
    // Stok senkronizasyon butonları
    document.querySelectorAll('[data-sync-stock]').forEach(button => {
        button.addEventListener('click', function() {
            const stokKodu = this.dataset.syncStock;
            this.disabled = true;
            
            syncStock(stokKodu)
                .finally(() => {
                    this.disabled = false;
                });
        });
    });
    
    // Fiyat senkronizasyon butonları
    document.querySelectorAll('[data-sync-price]').forEach(button => {
        button.addEventListener('click', function() {
            const stokKodu = this.dataset.syncPrice;
            this.disabled = true;
            
            syncPrice(stokKodu)
                .finally(() => {
                    this.disabled = false;
                });
        });
    });
    
    // Senkronizasyon butonları
    const syncAllButton = document.getElementById('sync-all-button');
    if (syncAllButton) {
        syncAllButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/sync/all', { method: 'POST' });
                if (!response.ok) throw new Error('Senkronizasyon başlatılamadı');
                
                const data = await response.json();
                showToast('success', 'Senkronizasyon başlatıldı');
                
            } catch (error) {
                console.error('Senkronizasyon hatası:', error);
                showToast('error', 'Senkronizasyon hatası: ' + error.message);
            }
        });
    }
    
    // Stok/Fiyat güncelleme butonu
    const syncStockPricesButton = document.getElementById('sync-stock-prices-button');
    if (syncStockPricesButton) {
        syncStockPricesButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/sync/stock-prices', { method: 'POST' });
                if (!response.ok) throw new Error('Güncelleme başlatılamadı');
                
                const data = await response.json();
                showToast('success', 'Stok ve fiyat güncellemesi başlatıldı');
                
            } catch (error) {
                console.error('Güncelleme hatası:', error);
                showToast('error', 'Güncelleme hatası: ' + error.message);
            }
        });
    }
    
    // Bağlantı test butonu
    const testConnectionButton = document.getElementById('test-connection-button');
    if (testConnectionButton) {
        testConnectionButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/test-connection');
                if (!response.ok) throw new Error('Bağlantı testi başarısız');
                
                const data = await response.json();
                showToast('success', 'Bağlantılar başarıyla test edildi');
                
            } catch (error) {
                console.error('Bağlantı test hatası:', error);
                showToast('error', 'Bağlantı test hatası: ' + error.message);
            }
        });
    }
});
