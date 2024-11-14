from odoo import api, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools import convert

class PosDemoConfig(models.Model):
    _name = 'pos.demo.config'
    # _inherit = ['pos.bus.mixin', 'pos.load.mixin']
    _description = 'Foodshop Demo Configuration'
    _check_company_auto = True

    @api.model
    def load_onboarding_foodshop_scenario(self):
        ref_name = 'point_of_sale.pos_config_foodshop'
        print("Loading: " + ref_name)
        if not self.env.ref(ref_name, raise_if_not_found=False):
            convert.convert_file(self.env, 'pos_demo', 'data/scenarios/foodshop_data.xml', None, mode='init', noupdate=False, kind='data')

        journal, payment_methods_ids = self._create_journal_and_payment_methods()
        bakery_categories = self.get_categories([
            'point_of_sale.pos_category_breads',
            'point_of_sale.pos_category_pastries',
        ])
        config = self.env['pos.config'].create({
            'name': _('Food Shop'),
            'company_id': self.env.company.id,
            'journal_id': journal.id,
            'payment_method_ids': payment_methods_ids,
            'limit_categories': True,
            'iface_available_categ_ids': bakery_categories,
        })
        self.env['ir.model.data']._update_xmlids([{
            'xml_id': self._get_suffixed_ref_name(ref_name),
            'record': config,
            # 'noupdate': True,
        }])

    @api.model
    def get_categories(self, categories):
        # filters out unavailable external id
        return [self.env.ref(category).id for category in categories if self.env.ref(category, raise_if_not_found=False)]

    @api.model
    def _get_suffixed_ref_name(self, ref_name):
        """Suffix the given ref_name with the id of the current company if it's not the main company."""
        main_company = self.env.ref('base.main_company', raise_if_not_found=False)
        if main_company and self.env.company.id == main_company.id:
            return ref_name
        else:
            return f"{ref_name}_{self.env.company.id}"

    @api.model
    def _create_cash_payment_method(self):
        cash_journal = self.env['account.journal'].create({
            'name': _('Cash'),
            'type': 'cash',
            'company_id': self.env.company.id,
        })
        return self.env['pos.payment.method'].create({
            'name': _('Cash'),
            'journal_id': cash_journal.id,
            'company_id': self.env.company.id,
        })

    @api.model
    def _create_journal_and_payment_methods(self, cash_ref=None):
        """This should only be called at creation of a new pos.config."""

        journal = self.env['account.journal']._ensure_company_account_journal()
        payment_methods = self.env['pos.payment.method']

        # create cash payment method per config
        cash_pm_from_ref = cash_ref and self.env.ref(cash_ref, raise_if_not_found=False)
        if cash_pm_from_ref:
            try:
                cash_pm_from_ref.check_access('read')
                cash_pm = cash_pm_from_ref
            except AccessError:
                cash_pm = self._create_cash_payment_method()
        else:
            cash_pm = self._create_cash_payment_method()

        if cash_ref and cash_pm != cash_pm_from_ref:
            self.env['ir.model.data']._update_xmlids([{
                'xml_id': cash_ref,
                'record': cash_pm,
                'noupdate': True,
            }])

        payment_methods |= cash_pm

        # only create bank and customer account payment methods per company
        bank_pm = self.env['pos.payment.method'].search([('journal_id.type', '=', 'bank'), ('company_id', '=', self.env.company.id)])
        if not bank_pm:
            bank_journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.env.company.id)], limit=1)
            if not bank_journal:
                raise UserError(_('Ensure that there is an existing bank journal. Check if chart of accounts is installed in your company.'))
            bank_pm = self.env['pos.payment.method'].create({
                'name': _('Card'),
                'journal_id': bank_journal.id,
                'company_id': self.env.company.id,
                'sequence': 1,
            })

        payment_methods |= bank_pm

        pay_later_pm = self.env['pos.payment.method'].search([('journal_id', '=', False), ('company_id', '=', self.env.company.id)])
        if not pay_later_pm:
            pay_later_pm = self.env['pos.payment.method'].create({
                'name': _('Customer Account'),
                'company_id': self.env.company.id,
                'split_transactions': True,
                'sequence': 2,
            })

        payment_methods |= pay_later_pm

        return journal, payment_methods.ids
