# This file is part of product_price_with_tax module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
from trytond.config import config
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Template']
__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active', True),
    }
DEPENDS = ['active']
DIGITS = int(config.get('digits', 'unit_price_digits', 4))


class Template:
    __name__ = "product.template"
    list_price_with_tax = fields.Property(fields.Numeric('List Price With Tax',
            states=STATES, digits=(16, DIGITS), depends=DEPENDS)
            )
    cost_price_with_tax = fields.Property(fields.Numeric('Cost Price With Tax',
            states=STATES, digits=(16, DIGITS), depends=DEPENDS)
            )

    def get_list_price_with_tax(self):
        Tax = Pool().get('account.tax')
        if self.list_price:
            taxes = [Tax(t) for t in self.get_taxes('customer_taxes_used')]
            taxes = Tax.compute(taxes, self.list_price, 1.0)
            tax_amount = sum([t['amount'] for t in taxes], Decimal('0.0'))
            return self.list_price + tax_amount

    @fields.depends('taxes_category', 'category', 'list_price',
        'customer_taxes')
    def on_change_list_price(self):
        try:
            changes = super(Template, self).on_change_list_price()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        return changes

    def get_list_price(self):
        Tax = Pool().get('account.tax')
        taxes = [Tax(t) for t in self.get_taxes('customer_taxes_used')]
        tax_amount = Tax.reverse_compute(self.list_price_with_tax, taxes)
        return tax_amount.quantize(Decimal(str(10.0 ** -DIGITS)))

    @fields.depends('taxes_category', 'category', 'list_price_with_tax',
        'customer_taxes')
    def on_change_list_price_with_tax(self):
        changes = {}
        if self.list_price_with_tax:
            changes['list_price'] = self.get_list_price()
        return changes

    def get_cost_price_with_tax(self):
        Tax = Pool().get('account.tax')
        if self.cost_price:
            taxes = [Tax(t) for t in self.get_taxes('supplier_taxes_used')]
            taxes = Tax.compute(taxes, self.cost_price, 1.0)
            tax_amount = sum([t['amount'] for t in taxes], Decimal('0.0'))
            return self.cost_price + tax_amount

    @fields.depends('taxes_category', 'category', 'cost_price',
        'supplier_taxes')
    def on_change_cost_price(self):
        try:
            changes = super(Template, self).on_change_cost_price()
        except AttributeError:
            changes = {}
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    def get_cost_price(self):
        Tax = Pool().get('account.tax')
        taxes = [Tax(t) for t in self.get_taxes('supplier_taxes_used')]
        tax_amount = Tax.reverse_compute(self.cost_price_with_tax, taxes)
        return tax_amount.quantize(Decimal(str(10.0 ** -DIGITS)))

    @fields.depends('taxes_category', 'category', 'cost_price_with_tax',
        'supplier_taxes')
    def on_change_cost_price_with_tax(self):
        changes = {}
        if self.cost_price_with_tax:
            changes['cost_price'] = self.get_cost_price()
        return changes

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'customer_taxes', 'supplier_taxes')
    def on_change_taxes_category(self):
        try:
            changes = super(Template, self).on_change_taxes_category()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    @fields.depends('taxes_category', 'list_price', 'cost_price',
        'customer_taxes')
    def on_change_customer_taxes(self):
        try:
            changes = super(Template, self).on_change_taxes_category()
        except AttributeError:
            changes = {}
        if self.list_price:
            changes['list_price_with_tax'] = self.get_list_price_with_tax()
        return changes

    @fields.depends('taxes_category', 'list_price', 'cost_price',
        'supplier_taxes')
    def on_change_supplier_taxes(self):
        try:
            changes = super(Template, self).on_change_taxes_category()
        except AttributeError:
            changes = {}
        if self.cost_price:
            changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes

    @fields.depends('taxes_category', 'category', 'list_price', 'cost_price',
        'customer_taxes', 'supplier_taxes')
    def on_change_category(self):
        try:
            changes = super(Template, self).on_change_category()
        except AttributeError:
            changes = {}
        if self.taxes_category:
            changes['list_price_with_tax'] = None
            changes['cost_price_with_tax'] = None
            if self.category:
                changes['list_price_with_tax'] = self.get_list_price_with_tax()
                changes['cost_price_with_tax'] = self.get_cost_price_with_tax()
        return changes
