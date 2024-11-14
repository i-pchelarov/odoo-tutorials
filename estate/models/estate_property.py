# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero
# from .estate_property_offer import EstatePropertyOffer


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Estate property model"
    _order = "id desc"

    name = fields.Char('Property Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type")
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    description = fields.Text('Description')
    postcode = fields.Char('Postcode')
    date_available = fields.Date('Available from', copy=False,
                                 default=fields.Date.today() + relativedelta(months=3)
                                 )
    expected_price = fields.Float('Expected price')
    selling_price = fields.Float('Actual price', readonly=True, copy=False)
    bedrooms = fields.Integer('Bedrooms', default=2)
    living_area = fields.Integer('Living area')
    garden_area = fields.Integer('Garden area')
    facades = fields.Integer('Facades')
    garage = fields.Boolean('With garage')
    garden = fields.Boolean('With garden')
    total_area = fields.Float('Total area', compute='_compute_total_area')

    garden_orientation = fields.Selection(
        string='Garden orientation',
        selection=[('north', 'North'), ('west', 'West'), ('south', 'South'), ('east', 'East')],
        help="Orientation of the garden, if any")
    state = fields.Selection(
        string='Offer state',
        selection=[('new', 'New'),
                   ('received', 'Offer received'),
                   ('accepted', 'Offer accepted'),
                   ('sold', 'Sold'),
                   ('cancelled', 'Cancelled')
                   ],
        help="Current state of the estate offer",
        required=True,
        copy=False,
        default='new'
    )

    salesperson_id = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    best_offer_price = fields.Float('Best offer', compute = "_compute_best_offer")

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price >= 0)',
         'The price of a property must be positive.'),
        ('check_sell_price', 'CHECK(selling_price >= 0)',
         'The price of a property must be positive.')
    ]

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_expected_price(self):
        for record in self:
            if not float_is_zero(record.selling_price, precision_rounding=0.01) and float_compare(record.selling_price, 0.9 * record.expected_price, precision_rounding=0.01) < 0:
                raise ValidationError('The actual price should not be less than 90% of the expected price.')

    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends("offer_ids.price")
    def _compute_best_offer(self):
        for record in self:
            best = max(record.mapped('offer_ids.price'), default=0)
            record.best_offer_price = best

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = None

    @api.ondelete(at_uninstall=False)
    def _unlink_except_state_active(self):
        for record in self:
            if record.state not in ['new', 'cancelled']:
                raise ValidationError('This property state does not allow deleting.')

    def action_sold(self):
        return True

    def action_property_sold(self):
        print("estate property sold.")
        for record in self:
            if record.state == 'cancelled':
                raise ValidationError('This property is cancelled, it cannot be sold.')
            else:
                record.state = 'sold'
        return True

    def action_property_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise ValidationError('This property is sold, it cannot be cancelled.')
            else:
                record.state = 'cancelled'
        return True

    def _check_add_offer(self, vals):
        for offer in self.offer_ids:
            if vals['price'] < offer.price:
                raise ValidationError('Cannot add offer with lower price, than existing.')

    def accept_offer(self, offer):
        if offer.property_id != self:
            raise UserError('The offer is not for this property!')
        elif self.state == 'sold' or self.state == 'cancelled':
            raise UserError('The property is complete. It cannot accept offers.')
        else:
            self.selling_price = offer.price
            self.buyer_id = offer.partner_id
            self.state = 'accepted'