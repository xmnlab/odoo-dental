FROM odoo:18.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /etc/odoo \
    && chown -R odoo:odoo /etc/odoo

COPY addons/thirdparty /mnt/extra-addons/

RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
