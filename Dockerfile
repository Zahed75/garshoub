FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libpq-dev \
    libcairo2-dev \
    pkg-config \
    postgresql-client \
    curl \
    node-less \
    git \
    xz-utils \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    && curl -L http://archive.ubuntu.com/ubuntu/pool/main/o/openssl/libssl1.1_1.1.1f-1ubuntu2_amd64.deb -o libssl1.1.deb \
    && dpkg -i libssl1.1.deb || apt-get install -f -y \
    && curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb -o wkhtmltox.deb \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm libssl1.1.deb wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/*

# Create odoo user
RUN useradd -m -d /opt/odoo -s /bin/bash odoo

# Set working directory
WORKDIR /opt/odoo

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Setup directories and permissions
RUN mkdir -p /var/lib/odoo /var/log/odoo && \
    chown -R odoo:odoo /var/lib/odoo /var/log/odoo /opt/odoo

# Make entrypoint and odoo-bin executable
RUN chmod +x /opt/odoo/entrypoint.sh /opt/odoo/odoo-bin

# Switch to odoo user
USER odoo

# Expose Odoo ports
EXPOSE 8069 8072

# Entrypoint script
ENTRYPOINT ["/opt/odoo/entrypoint.sh"]

# Run Odoo
CMD /opt/odoo/odoo-bin -c /opt/odoo/odoo.conf -d "${DB_NAME:-Garshoub HQ}" --data-dir /var/lib/odoo