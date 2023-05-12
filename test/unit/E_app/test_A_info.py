"""
Test the process_file function
"""

import tempfile
from pathlib import Path


import pii_extract.app.task_info as mod


CONFIGFILE = Path(__file__).parents[2] / "data" / "tasklist-example.json"


INFO = """. Built tasks [language=en]

 CREDIT_CARD   
   Language: any
   Country: any
   Name: standard credit card
     A simple credit card number detection for most international credit cards

 PHONE_NUMBER   international phone number
   Language: en
   Country: any
   Name: regex for PHONE_NUMBER:international phone number
     detect phone numbers that use international notation. Uses context
"""

# -------------------------------------------------------------------------

def test100_app_info(capfd):
    """
    Test base constructor
    """
    with tempfile.NamedTemporaryFile(suffix=".json") as f1:
        f1.close()
        args = ["list-tasks", "--config", str(CONFIGFILE),
                "--lang", "en", "--skip-plugins"]
        mod.main(args)

    captured = capfd.readouterr()
    #print("*** CAPTURED", captured.out, sep="\n")
    assert captured.out == INFO
