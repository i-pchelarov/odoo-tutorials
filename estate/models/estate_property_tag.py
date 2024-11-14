from odoo import fields, models

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "Tag for marking an estate property"
    _order = "name"

    name = fields.Char('Property Tag', required=True, translate=True)
