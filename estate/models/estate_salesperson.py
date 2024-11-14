from odoo import api, fields, models, exceptions

class EstateSalesperson(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many('estate.property', 'salesperson_id', string = "Estate Properties", domain = "[('state', 'in', ['new', 'received', 'accepted', 'sold'])]")
