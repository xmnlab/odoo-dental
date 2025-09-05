# odoonto

## Development

### Setup

#### Containers

```bash
$ sugar compose build
```

```bash
makim db.init
```

```bash
$ sugar compose-ext restart
```

To add a new language:

```bash
makim tasks.add-langs --langs es_BO
```

To add a new country and language:

```bash
$ makim odoo.l10n-apply --country-code base.es --l10n-modules account,l10n_es
```

To install dental module:

```bash
makim odoo.install-app --modules dental_clinic
```

For database managment, you can use the following link:
{http://localhost:8069/web/database/manager}
