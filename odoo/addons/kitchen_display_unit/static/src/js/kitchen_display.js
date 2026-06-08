let previousOrderIds = new Set();
let soundEnabled = true;

function toggleSound() {
    soundEnabled = !soundEnabled;
    const icon = document.getElementById('sound-icon');
    icon.className = soundEnabled ? 'fa fa-volume-up' : 'fa fa-volume-off';
    icon.parentElement.innerHTML = `<i class="${icon.className}" id="sound-icon"/> Sound ${soundEnabled ? 'ON' : 'OFF'}`;
}

function playNotificationSound() {
    if (!soundEnabled) return;
    const audio = document.getElementById('new-order-sound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
}

function getStatusClass(status) {
    const map = {
        'new': 'status-new',
        'in_progress': 'status-in_progress',
        'ready': 'status-ready',
        'delivered': 'status-delivered',
    };
    return map[status] || 'status-new';
}

function getStatusLabel(status) {
    const map = {
        'new': 'New',
        'in_progress': 'In Progress',
        'ready': 'Ready',
        'delivered': 'Delivered',
    };
    return map[status] || status;
}

function getActionButton(order) {
    if (order.status === 'new') {
        return `<button class="btn-start" onclick="updateStatus(${order.id}, 'in_progress')">Start Cooking</button>`;
    } else if (order.status === 'in_progress') {
        return `<button class="btn-ready" onclick="updateStatus(${order.id}, 'ready')">Ready for Delivery</button>`;
    } else if (order.status === 'ready') {
        return `<button class="btn-delivered" onclick="updateStatus(${order.id}, 'delivered')">Mark Delivered</button>`;
    }
    return '';
}

function renderOrders(orders) {
    const container = document.getElementById('orders-container');

    if (!orders || orders.length === 0) {
        container.innerHTML = `
            <div class="col-12 empty-state">
                <i class="fa fa-coffee"></i>
                <h3 class="text-muted">No active orders</h3>
                <p class="text-muted">New orders will appear here automatically.</p>
            </div>
        `;
        return;
    }

    let html = '';
    orders.forEach(order => {
        const linesHtml = order.lines.map(line => `
            <div class="product-item">
                <span class="product-name">${line.product_name}</span>
                <span class="product-qty">× ${line.quantity}</span>
            </div>
        `).join('');

        html += `
            <div class="col-md-6 col-lg-4">
                <div class="order-card status-${order.status}">
                    <div class="order-header">
                        <span class="order-ref">${order.name}</span>
                        <span class="status-badge ${getStatusClass(order.status)}">${getStatusLabel(order.status)}</span>
                    </div>
                    <div class="customer-info">
                        <h5><i class="fa fa-user"></i> ${order.partner_name}</h5>
                        ${order.partner_phone ? `<p><i class="fa fa-phone"></i> ${order.partner_phone}</p>` : ''}
                        ${order.delivery_address ? `<p><i class="fa fa-map-marker"></i> ${order.delivery_address}</p>` : ''}
                        <p class="order-time"><i class="fa fa-clock-o"></i> ${order.order_date}</p>
                    </div>
                    <div class="product-list">
                        ${linesHtml}
                    </div>
                    <div class="order-total">
                        Total: AED ${order.total_amount.toFixed(2)}
                    </div>
                    ${order.notes ? `<div class="alert alert-info py-1"><small><i class="fa fa-sticky-note"></i> ${order.notes}</small></div>` : ''}
                    <div class="action-buttons">
                        ${getActionButton(order)}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

async function fetchOrders() {
    try {
        const response = await fetch('/kitchen/orders', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {},
                id: Math.floor(Math.random() * 1000000),
            }),
        });
        const data = await response.json();
        if (data.result) {
            const orders = data.result.orders;

            // Check for new orders
            const currentIds = new Set(orders.map(o => o.id));
            const hasNewOrders = [...currentIds].some(id => !previousOrderIds.has(id));

            if (hasNewOrders && previousOrderIds.size > 0) {
                playNotificationSound();
            }

            previousOrderIds = currentIds;
            renderOrders(orders);

            // Update timestamp
            document.getElementById('last-updated').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
        }
    } catch (error) {
        console.error('Failed to fetch orders:', error);
    }
}

async function updateStatus(orderId, status) {
    try {
        const response = await fetch('/kitchen/order/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: { order_id: orderId, status: status },
                id: Math.floor(Math.random() * 1000000),
            }),
        });
        const data = await response.json();
        if (data.result && data.result.success) {
            fetchOrders();
        }
    } catch (error) {
        console.error('Failed to update order:', error);
    }
}

// Initial load
fetchOrders();

// Auto-refresh every 30 seconds
setInterval(fetchOrders, 30000);
