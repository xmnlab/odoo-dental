#!/usr/bin/env python3
"""
Usage:
  apply_l10n.py <odoo.conf> <db_name> <base.xx> <modules_csv>

Examples
--------
  python3 apply_l10n.py /etc/odoo/odoo.conf odoodb base.fr account,l10n_fr
  python3 apply_l10n.py /etc/odoo/odoo.conf odoodb base.br account,l10n_br
"""

from __future__ import annotations

import contextlib
import sys

import odoo

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry


def _resolve_xmlid(env: api.Environment, xmlid: str):
    """Return record for xmlid or None if it doesn't exist."""
    try:
        return env.ref(xmlid)
    except Exception:
        return None


def main() -> None:
    if len(sys.argv) < 5:
        print(
            'Usage: apply_l10n.py <odoo.conf> <db_name> <base.xx> <modules_csv>'
        )
        sys.exit(2)

    conf_path, db_name, country_xml, modules_csv = sys.argv[1:5]
    odoo.tools.config.parse_config(['-c', conf_path])
    modules = [m.strip() for m in modules_csv.split(',') if m.strip()]

    # Use Environment.manage() if available; otherwise a no-op context.
    manage_ctx = getattr(api.Environment, 'manage', None)
    ctx_mgr = (
        manage_ctx() if callable(manage_ctx) else contextlib.nullcontext()
    )

    with ctx_mgr:
        # ---------- PASS #1: set country and install requested modules ----------
        registry = Registry(db_name)
        with registry.cursor() as cr:
            base_env = api.Environment(cr, SUPERUSER_ID, {})

            # Pick a company (main if available, else first)
            Company = base_env['res.company']
            if hasattr(Company, '_get_main_company'):
                company = Company._get_main_company()
            else:
                company = Company.search([], limit=1)
            if not company:
                raise RuntimeError('No company found in database.')

            # Context targeting that company
            ctx = dict(base_env.context or {})
            ctx.update(
                {
                    'allowed_company_ids': [company.id],
                    'force_company': company.id,
                }
            )

            # Set company country
            country = _resolve_xmlid(base_env, country_xml)
            if not country:
                raise ValueError(f"Country XMLID '{country_xml}' not found.")
            company.write({'country_id': country.id})
            cr.commit()

            # Ensure required modules are installed (idempotent)
            if modules:
                mods = (
                    base_env['ir.module.module']
                    .sudo()
                    .search([('name', 'in', modules)])
                )
                to_install = mods.filtered(lambda m: m.state != 'installed')
                if to_install:
                    cr.commit()
                    to_install.button_immediate_install()
                    # module install triggers a registry reload

        # Re-fetch a fresh registry AFTER installs
        registry = Registry(db_name)

        # ---------- PASS #2: choose chart template and load CoA ----------
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, ctx)

            Company = env['res.company']
            if hasattr(Company, '_get_main_company'):
                company = Company._get_main_company()
            else:
                company = Company.search([], limit=1)

            # Check if accounts already exist for this company; be robust if model/field differs
            accounts_exist = False
            account_model = env.registry.models.get('account.account')
            if account_model:
                Account = env['account.account']
                domain = []
                if 'company_id' in Account._fields:
                    domain = [('company_id', '=', company.id)]
                # If there is no company_id field, just check any account presence
                accounts_exist = bool(Account.sudo().search_count(domain))
            # If accounts exist, skip loading a chart
            if accounts_exist:
                print(
                    'Accounts already present for this company; skipping chart load.'
                )
                cr.commit()
                print('Localization applied ✓')
                return

            # Robust chart template lookup
            tmpl_model = env['account.chart.template']
            domain = []
            if company.country_id:
                if 'country_id' in tmpl_model._fields:  # older schema
                    domain = [('country_id', '=', company.country_id.id)]
                elif 'country_ids' in tmpl_model._fields:  # newer schema (m2m)
                    domain = [('country_ids', 'in', [company.country_id.id])]

            tmpl = tmpl_model.search(domain, limit=1)

            # Try common XML IDs from provided l10n modules
            if not tmpl and modules:
                for mod in modules:
                    cand = _resolve_xmlid(
                        env, f'{mod}.configurable_chart_template'
                    )
                    if (
                        cand is not None
                        and cand._name == 'account.chart.template'
                    ):
                        tmpl = cand
                        break

            # Generic fallback(s)
            if not tmpl:
                generic = _resolve_xmlid(
                    env, 'l10n_generic_coa.configurable_chart_template'
                )
                tmpl = generic or tmpl_model.search([], limit=1)

            if not tmpl:
                raise ValueError(
                    'No account.chart.template found. Ensure your l10n module '
                    "(e.g., 'account,l10n_fr') is installed before applying localization."
                )

            # Load the chart of accounts for this company
            tmpl._load_for_current_company()
            cr.commit()
            print('Localization applied ✓')


if __name__ == '__main__':
    main()
