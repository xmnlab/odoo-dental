FROM odoo:18.0

USER root

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    unzip \
    ca-certificates \
    git \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /etc/odoo \
  && chown -R odoo:odoo /etc/odoo

COPY addons/thirdparty/* /mnt/extra-addons/
COPY addons/_scripts/apply_l10n.py /mnt/extra-addons/

RUN cd /mnt/extra-addons/ \
  && git clone -o dental_clinic --depth 1 https://github.com/ambientWave/Odoo-Dental-Clinic-Managment-System-With-REST-API.git

RUN chown -R odoo:odoo /mnt/extra-addons

USER odoo
