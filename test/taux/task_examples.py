"""
Some task example definitions for unit tests
"""

from pii_data.types import PiiEnum

from taux.modules.any.credit_card import CreditCard
from taux.modules.en.any.international_phone_number import PATTERN_INT_PHONE
from taux.modules.en.au.tfn import tax_file_number

# -------------------------------------------------------------------------

TASK_PHONE_NUMBER = {
    'lang': 'en',
    'country': 'any',
    'pii': PiiEnum.PHONE_NUMBER,
    'type': 'regex',
    'task': PATTERN_INT_PHONE,
    'name': 'international phone number',
    'doc': 'detect phone numbers that use international notation. Uses context',
    'context': {'value': ['ph', 'phone', 'fax'],
                'width': [16, 0], 'type': 'word'}
}

TASK_GOVID = {
    'lang': 'en',
    'country': 'au',
    'pii': PiiEnum.GOV_ID,
    'type': 'callable',
    'task': tax_file_number,
    'name': 'tax file number',
    'doc': 'Australian Tax File Number (detect and validate)'
}

TASK_CREDIT_CARD = {
    'lang': 'any',
    'country': 'any',
    'pii': PiiEnum.CREDIT_CARD,
    'type': 'PiiTask',
    'task': CreditCard,
    'name': 'standard credit card',
    'doc': 'Credit card numbers for most international credit cards (detect & validate)'
}
