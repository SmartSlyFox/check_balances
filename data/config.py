import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

ABIS_DIR = os.path.join(ROOT_DIR, 'abis')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
TOKEN_ABI = os.path.join(ABIS_DIR, 'token.json')


rpc = 'https://ethereum-goerli.publicnode.com'

with open(f"{DATA_DIR}/wallets.txt", "r") as f:
    WALLETS = [row.strip() for row in f]
with open(f"{DATA_DIR}/recipients.txt", "r") as f:
    RECIPIENTS = [row.strip() for row in f]

dict_wallet_recipient = dict(zip(WALLETS, RECIPIENTS))
