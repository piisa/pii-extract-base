"""
Some examples of raw task descriptors for unit tests
"""

from pii_data.types import PiiEnum

from taux.modules.any.credit_card_mock import CreditCardMock
from taux.modules.en.any.international_phone_number import PATTERN_INT_PHONE
from taux.modules.en.au.tfn_ex import tax_file_number_example

# -------------------------------------------------------------------------

# As a flat object
TASK_PHONE_NUMBER = {
    'class': 'regex',
    'task': PATTERN_INT_PHONE,
    'name': 'international phone number',
    'doc': 'detect phone numbers that use international notation. Uses context',
    'pii': PiiEnum.PHONE_NUMBER,
    'lang': 'en',
    'country': 'any',
    'context': {'value': ['ph', 'phone', 'fax'],
                'width': [16, 0], 'type': 'word'}
}

# As a structured object
TASK_GOVID = {
    'class': 'callable',
    'task': tax_file_number_example,
    'name': 'Australian tax file number',
    'doc': 'Australian Tax File Number (detect and validate)',
    'pii': {
        'type': PiiEnum.GOV_ID,
        'lang': 'en',
        'country': 'au'
        #'subtype': 'tax file number',
    }
}

# As a flat object, pii is a string
TASK_CREDIT_CARD = {
    'class': 'PiiTask',
    'task': CreditCardMock,
    'name': 'standard credit card',
    'doc': 'Credit card numbers for most international credit cards (detect & validate)',
    'pii': "CREDIT_CARD",
    'lang': 'any',
    'country': 'any'
}
