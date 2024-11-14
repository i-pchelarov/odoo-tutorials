from odoo import fields, models

class EstatePropertyType(models.Model):
    _name = "estate.property.type"
    _description = "Type of estate property: house, apartment, etc."
    _order = "sequence, name"

    name = fields.Char('Property Type', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
