"""
Some examples of finalized task descriptors for unit tests
"""

from pii_data.types import PiiEnum

from taux.modules.any.credit_card_mock import CreditCardMock
from taux.modules.en.any.international_phone_number import PATTERN_INT_PHONE
from taux.modules.en.au.tfn import tax_file_number

# -------------------------------------------------------------------------

TASK_PHONE_NUMBER = {
    'obj': {
        'class': 'regex',
        'task': PATTERN_INT_PHONE,
    },
    'info': {    
        'name': 'international phone number',
        'doc': 'detect phone numbers that use international notation. Uses context'
    },
    'piid': {
        'pii': PiiEnum.PHONE_NUMBER,
        'lang': 'en',
        'country': 'any',
        'context': {'value': ['ph', 'phone', 'fax'],
                    'width': [16, 0], 'type': 'word'},
        'method': 'regex,context'
    }
}

TASK_GOVID = {
    'obj': {
        'class': 'callable',
        'task': tax_file_number
    },
    'info': {
        'name': 'tax file number',
        'doc': 'Australian Tax File Number (detect and validate)'
    },
    'piid': {
        'pii': PiiEnum.GOV_ID,
        'lang': 'en',
        'country': 'au'
        #'subtype': 'tax file number'
    }
}

TASK_CREDIT_CARD = {
    'obj': {
        'class': 'piitask',
        'task': CreditCardMock,
    },
    'info': {
        'name': 'standard credit card',
        'doc': 'A simple credit card number detection for most international credit cards',
    },
    'piid': {
        'pii': PiiEnum.CREDIT_CARD,
        'lang': 'any',
        'country': 'any'
    }
}

TASK_ERR = {
    'obj': {
        'class': 'not-a-valid-type',
        'task': CreditCardMock,
    },
    'info': {
        'name': 'standard credit card',
    },
    'piid': {
        'pii': "CREDIT_CARD"
    }
}

