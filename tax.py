# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import datetime
from collections import namedtuple
from decimal import Decimal

from sql import Null
from sql.aggregate import Sum
from itertools import groupby

from trytond.model import ModelView, ModelSQL, MatchMixin, fields
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond import backend
from trytond.pyson import Eval, If, Bool, PYSONEncoder
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta

__all__ = ['Tax']
__metaclass__ = PoolMeta

class Tax(ModelSQL, ModelView):
    __name__ = 'account.tax'

    update_unit_price = fields.Boolean('Update Unit Price',
        states={
            'invisible': Bool(Eval('parent')),
            },
        depends=['parent'],
        help=('If checked then the unit price for further tax computation will'
            'be modified by this tax'))

    @classmethod
    def __setup__(cls):
        super(Tax, cls).__setup__()

    def _group_taxes(self):
        'Key method used to group taxes'
        return (self.sequence,)

    @classmethod
    def _reverse_rate_amount(cls, taxes, date):
        rate, amount = 0, 0
        for tax in taxes:
            start_date = tax.start_date or datetime.date.min
            end_date = tax.end_date or datetime.date.max
            if not (start_date <= date <= end_date):
                continue

            if tax.type == 'percentage':
                rate += tax.rate
            elif tax.type == 'fixed':
                amount += tax.amount

            if tax.childs:
                child_rate, child_amount = cls._reverse_rate_amount(
                    tax.childs, date)
                rate += child_rate
                amount += child_amount
        return rate, amount

    @classmethod
    def _reverse_unit_compute(cls, price_unit, taxes, date):
        rate, amount = 0, 0
        update_unit_price = False
        unit_price_variation_amount = 0
        unit_price_variation_rate = 0
        for _, group_taxes in groupby(taxes, key=cls._group_taxes):
            group_taxes = list(group_taxes)
            g_rate, g_amount = cls._reverse_rate_amount(group_taxes, date)
            if update_unit_price:
                g_amount += unit_price_variation_amount * g_rate
                g_rate += unit_price_variation_rate * g_rate

            g_update_unit_price = any(t.update_unit_price for t in group_taxes)
            update_unit_price |= g_update_unit_price
            if g_update_unit_price:
                unit_price_variation_amount += g_amount
                unit_price_variation_rate += g_rate

            rate += g_rate
            amount += g_amount

        return (price_unit - amount) / (1 + rate)

    @classmethod
    def sort_taxes(cls, taxes, reverse=False):
        '''
        Return a list of taxes sorted
        '''
        return sorted(taxes, key=lambda t: (t.sequence, t.id), reverse=reverse)

    @classmethod
    def compute(cls, taxes, price_unit, quantity, date=None):
        '''
        Compute taxes for price_unit and quantity at the date.
        Return list of dict for each taxes and their childs with:
            base
            amount
            tax
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        if date is None:
            date = Date.today()
        taxes = cls.sort_taxes(taxes)
        res = cls._unit_compute(taxes, price_unit, date)
        quantity = Decimal(str(quantity or 0.0))
        for row in res:
            row['base'] *= quantity
            row['amount'] *= quantity
        return res

    @classmethod
    def reverse_compute(cls, price_unit, taxes, date=None):
        '''
        Reverse compute the price_unit for taxes at the date.
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        if date is None:
            date = Date.today()
        taxes = cls.sort_taxes(taxes)
        return cls._reverse_unit_compute(price_unit, taxes, date)
