from odoo import api, fields, models, exceptions
from datetime import timedelta, datetime

from .estate_property import EstateProperty

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Offer to buy an estate property"
    _order = "price desc"

    price = fields.Float('Price', required=True)
    status = fields.Selection(
        string="Status",
        selection=[
            ('declined', 'Offer declined'),
            ('accepted', 'Offer accepted')
        ],
        copy=False
    )
    partner_id = fields.Many2one("res.partner", string="Buyer", required=True)
    property_id = fields.Many2one("estate.property", string="Property", required=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id")
    validity = fields.Integer('Valid for', default=7)
    date_expire = fields.Date('Expiration date', compute = '_compute_expire_date', inverse = '_inverse_expire_date')

    @api.model
    def create(self, vals):
        self._check_offer_add(vals)
        print(vals)
        property = self.env['estate.property'].browse(vals['property_id'])
        if property:
            property.state = 'received'

        return super().create(vals)


    def _check_offer_add(self, vals):
        property = self.env['estate.property'].browse(vals['property_id'])
        property._check_add_offer(vals)
        pass

    @api.depends('validity')
    def _compute_expire_date(self):
        for record in self:
            created = record.create_date or fields.Date.today()
            record.date_expire = created + timedelta(days=record.validity)

    def _inverse_expire_date(self):
        for record in self:
            created = record.create_date or datetime.now()
            delta = record.date_expire - created.date()
            record.validity = delta.days

    def action_accept(self):
        for record in self:
            if self._find_accepted_offer(record.property_id):
                raise exceptions.UserError('There is an offer already accepted.')
            else:
                record.status = 'accepted'
                record.property_id.accept_offer(record)
        return True

    def action_decline(self):
        for record in self:
            record.status = 'declined'
        return True

    def _find_accepted_offer(self, property_id: EstateProperty):
        for offer in property_id.offer_ids:
            if offer.status == 'accepted':
                return offer
        return None
