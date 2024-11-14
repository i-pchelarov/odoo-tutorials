from odoo import models, exceptions, _
from odoo import Command

class EstateAccount(models.Model):
    _inherit = "estate.property"

    def action_property_sold(self):
        sold = super().action_property_sold()
        self.create_invoice()
        return sold

    def create_invoice(self):
        move_type = 'out_invoice'
        partner_id = self.buyer_id.id
        print(self.env['account.move']._name)
        move = self.env['account.move']
        journal = move._search_default_journal()
        # self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        print([journal.id, journal.type, move._get_valid_journal_types()])

        if not journal:
            raise exceptions.UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.salesperson_id.name, self.salesperson_id.id))

        invoice_vals = {
                'move_type': move_type,
                'partner_id': partner_id,
                'journal_id': 13,
                "line_ids": [
                    Command.create({
                        "name": "Авансово плащане за " + self.name,
                        "quantity": "0.06",
                        "price_unit": self.selling_price
                    }),
                    Command.create({
                        "name": "Административна такса",
                        "quantity": "1",
                        "price_unit": 100
                    })
                ],
                }

        moves = move.create(invoice_vals)

        return moves