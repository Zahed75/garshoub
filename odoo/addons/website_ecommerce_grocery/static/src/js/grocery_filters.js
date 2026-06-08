/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.grocery-filters button');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const filter = this.dataset.filter;

            // Update active state
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // Filter products (basic implementation)
            const products = document.querySelectorAll('.oe_product');
            products.forEach(product => {
                if (filter === 'all') {
                    product.style.display = '';
                } else {
                    // Check if product belongs to category
                    const categoryLinks = product.querySelectorAll('a');
                    let hasCategory = false;
                    categoryLinks.forEach(link => {
                        if (link.href && link.href.includes('/shop/category/' + filter)) {
                            hasCategory = true;
                        }
                    });
                    product.style.display = hasCategory ? '' : 'none';
                }
            });
        });
    });
});
