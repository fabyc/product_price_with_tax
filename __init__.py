# This file is part of product_price_with_tax module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from .product import *
from .tax import *

def register():
    Pool.register(
        Tax,
        Template,
        module='product_price_with_tax', type_='model')
