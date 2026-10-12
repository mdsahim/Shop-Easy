/**
 * ShopEasy - Modern E-Commerce Client Scripts
 */

// Helper to retrieve CSRF token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Toast Notification Manager
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container-custom';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `custom-toast toast-${type}`;
  toast.innerHTML = `
    <div class="d-flex align-items-center gap-2">
      <i class="bi ${type === 'success' ? 'bi-check-circle-fill text-success' : 'bi-exclamation-triangle-fill text-danger'} fs-5"></i>
      <span class="fw-medium">${message}</span>
    </div>
    <button type="button" class="btn-close ms-2" aria-label="Close"></button>
  `;

  const closeBtn = toast.querySelector('.btn-close');
  closeBtn.addEventListener('click', () => {
    toast.remove();
  });

  container.appendChild(toast);

  // Auto remove after 3.5 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Update cart badge counter everywhere
function updateCartCountBadge(count) {
  const badges = document.querySelectorAll('.cart-badge-count');
  badges.forEach(badge => {
    badge.textContent = count;
    if (count > 0) {
      badge.classList.remove('d-none');
    } else {
      badge.classList.add('d-none');
    }
    // Subtle bounce effect
    badge.animate([
      { transform: 'scale(1)' },
      { transform: 'scale(1.3)' },
      { transform: 'scale(1)' }
    ], { duration: 250 });
  });
}

// Handle Add-To-Cart buttons with AJAX
function setupAddToCartButtons() {
  document.querySelectorAll('.ajax-add-to-cart').forEach(form => {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;

      // Disable button and show spinner
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';

      const actionUrl = this.action;
      const formData = new FormData(this);

      try {
        const response = await fetch(actionUrl, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: formData
        });

        const data = await response.json();

        if (data.success) {
          showToast(data.message, 'success');
          if (data.cart_count !== undefined) {
            updateCartCountBadge(data.cart_count);
          }
        } else {
          showToast(data.message, 'error');
        }
      } catch (err) {
        // Fallback to normal submission if network error
        this.submit();
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
      }
    });
  });
}

// Handle Cart Quantity updates (+ and -) on cart page
function setupCartQuantityPickers() {
  document.querySelectorAll('.cart-item-row').forEach(row => {
    const productId = row.dataset.productId;
    const input = row.querySelector('.cart-qty-input');
    const btnDec = row.querySelector('.btn-qty-dec');
    const btnInc = row.querySelector('.btn-qty-inc');
    const itemTotalEl = row.querySelector('.item-line-total');

    if (!input || !productId) return;

    const maxStock = parseInt(input.getAttribute('max')) || 999;

    async function sendUpdate(action, exactQty = null) {
      const formData = new FormData();
      if (action) formData.append('action', action);
      if (exactQty !== null) formData.append('quantity', exactQty);

      try {
        const response = await fetch(`/cart/update/${productId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: formData
        });
        const data = await response.json();

        if (data.success) {
          if (data.item_quantity <= 0) {
            row.remove();
            showToast(data.message, 'success');
            // Check if cart is now empty
            if (document.querySelectorAll('.cart-item-row').length === 0) {
              window.location.reload();
            }
          } else {
            input.value = data.item_quantity;
            if (itemTotalEl && data.item_total) {
              itemTotalEl.textContent = `$${parseFloat(data.item_total).toFixed(2)}`;
            }
          }

          // Update summary totals
          updateCartSummary(data);
          updateCartCountBadge(data.cart_count);
        } else {
          showToast(data.message, 'error');
        }
      } catch (e) {
        window.location.reload();
      }
    }

    if (btnDec) {
      btnDec.addEventListener('click', () => sendUpdate('decrement'));
    }
    if (btnInc) {
      btnInc.addEventListener('click', () => {
        const curr = parseInt(input.value) || 1;
        if (curr >= maxStock) {
          showToast(`Maximum stock limit reached (${maxStock})`, 'error');
          return;
        }
        sendUpdate('increment');
      });
    }
    input.addEventListener('change', () => {
      let val = parseInt(input.value);
      if (isNaN(val) || val < 1) val = 1;
      if (val > maxStock) {
        val = maxStock;
        showToast(`Quantity capped at maximum available stock (${maxStock})`, 'error');
      }
      sendUpdate(null, val);
    });
  });
}

// Update Cart page summary cards
function updateCartSummary(data) {
  const subtotalEl = document.getElementById('cartSubtotalAmount');
  const shippingEl = document.getElementById('cartShippingAmount');
  const totalEl = document.getElementById('cartTotalAmount');

  if (subtotalEl && data.subtotal) {
    subtotalEl.textContent = `$${parseFloat(data.subtotal).toFixed(2)}`;
  }
  if (shippingEl && data.shipping) {
    const shipVal = parseFloat(data.shipping);
    shippingEl.textContent = shipVal === 0 ? 'FREE' : `$${shipVal.toFixed(2)}`;
  }
  if (totalEl && data.total) {
    totalEl.textContent = `$${parseFloat(data.total).toFixed(2)}`;
  }
}

// Product Detail page quantity counter (+ / -)
function setupDetailQuantityCounter() {
  const input = document.getElementById('detailQuantityInput');
  const btnDec = document.getElementById('detailQtyDec');
  const btnInc = document.getElementById('detailQtyInc');

  if (input && btnDec && btnInc) {
    const maxStock = parseInt(input.getAttribute('max')) || 99;

    btnDec.addEventListener('click', () => {
      let val = parseInt(input.value) || 1;
      if (val > 1) {
        input.value = val - 1;
      }
    });

    btnInc.addEventListener('click', () => {
      let val = parseInt(input.value) || 1;
      if (val < maxStock) {
        input.value = val + 1;
      } else {
        showToast(`Maximum stock available is ${maxStock}`, 'error');
      }
    });
  }
}

// Checkout submit spinner
function setupCheckoutSubmitSpinner() {
  const form = document.getElementById('checkoutForm');
  if (form) {
    form.addEventListener('submit', function () {
      const btn = document.getElementById('btnPlaceOrder');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing Your Order...';
      }
    });
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  setupAddToCartButtons();
  setupCartQuantityPickers();
  setupDetailQuantityCounter();
  setupCheckoutSubmitSpinner();

  // Auto-dismiss standard alerts
  setTimeout(() => {
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        bsAlert.close();
      } catch (e) {}
    });
  }, 5000);
});
