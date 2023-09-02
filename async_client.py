from typing import Optional
import requests
from web3 import Web3, AsyncWeb3, AsyncHTTPProvider
from data.config import TOKEN_ABI
from models import TokenAmount
from utils import read_json
from asyncio import sleep


class Client:
    # default_abi = DefaultABIs.Token
    default_abi = read_json(TOKEN_ABI)

    def __init__(
            self,
            private_key: str,
            rpc: str
    ):
        self.private_key = private_key
        self.rpc = rpc
        self.w3 = AsyncWeb3(AsyncHTTPProvider(endpoint_uri=self.rpc))
        self.address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key=private_key).address)

    async def get_decimals(self, contract_address: str) -> int:
        return int(await self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=Client.default_abi
        ).functions.decimals().call())

    async def balance_of(self, contract_address: str, address: Optional[str] = None):
        if not address:
            address = self.address
        return await self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=Client.default_abi
        ).functions.balanceOf(address).call()

    async def get_allowance(self, token_address: str, spender: str):
        return await self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(token_address),
            abi=Client.default_abi
        ).functions.allowance(self.address, spender).call()

    async def check_balance_interface(self, token_address, min_value) -> bool:
        print(f'{self.address} | перевірка баланса {await self.get_symbol(token_address)} токена')
        balance = await self.balance_of(contract_address=token_address)
        decimal = await self.get_decimals(contract_address=token_address)
        if balance < min_value * 10 ** decimal:
            print(
                f'{self.address} | баланс {await self.get_symbol(token_address)} токена менше {min_value} {await self.get_symbol(token_address)}')
            return False
        return True

    async def send_transaction(
            self,
            to,
            data=None,
            from_=None,
            increase_gas=1.1,
            value=None
    ):
        if not from_:
            from_ = self.address

        tx_params = {
            'chainId': await self.w3.eth.chain_id,
            'nonce': await self.w3.eth.get_transaction_count(self.address),
            'from': AsyncWeb3.to_checksum_address(from_),
            'to': AsyncWeb3.to_checksum_address(to),
            'gasPrice': await self.w3.eth.gas_price
        }
        if data:
            tx_params['data'] = data
        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(await self.w3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            print(f'{self.address} | Transaction failed | {err}')
            return None

        sign = await self.w3.eth.account.sign_transaction(tx_params, self.private_key)
        return await self.w3.eth.send_raw_transaction(sign.rawTransaction)

    async def verif_tx(self, tx_hash) -> bool:
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if 'status' in data and data['status'] == 1:
                print(f'{self.address} | Транзакція успішна: {tx_hash.hex()}')
                return True
            else:
                print(f'{self.address} | Транзакція невдала {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            print(f'{self.address} | неочікувана помилка в функції <verif_tx> : {err}')
            return False

    async def approve(self, token_address, spender, amount: Optional[TokenAmount] = None):
        contract = await self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(token_address),
            abi=Client.default_abi
        )
        return await self.send_transaction(
            to=token_address,
            data=contract.encodeABI('approve',
                                    args=(
                                        spender,
                                        amount.Wei
                                    ))
        )

    async def approve_interface(self, token_address: str, spender: str, amount: Optional[TokenAmount] = None) -> bool:
        print(f'{self.address} | approve | start approve {token_address} for spender {spender}')
        decimals = await self.get_decimals(contract_address=token_address)
        balance = TokenAmount(
            amount=await self.balance_of(contract_address=token_address),
            decimals=decimals,
            wei=True
        )
        if balance.Wei <= 0:
            print(f'{self.address} | approve | zero balance')
            return False

        if not amount or amount.Wei > balance.Wei:
            amount = balance

        approved = TokenAmount(
            amount=await self.get_allowance(token_address=token_address, spender=spender),
            decimals=decimals,
            wei=True
        )
        if amount.Wei <= approved.Wei:
            print(f'{self.address} | approve | already approved')
            return True

        tx_hash = await self.approve(token_address=token_address, spender=spender, amount=amount)
        if not self.verif_tx(tx_hash=tx_hash):
            print(f'{self.address} | approve | {token_address} for spender {spender}')
            return False
        return True

    def get_eth_price(self, token='ETH'):
        token = token.upper()
        print(f'{self.address} | getting {token} price')
        response = requests.get(f'https://api.binance.com/api/v3/depth?limit=1&symbol={token}USDT')
        if response.status_code != 200:
            print(f'code: {response.status_code} | json: {response.json()}')
            return None
        result_dict = response.json()
        if 'asks' not in result_dict:
            print(f'code: {response.status} | json: {response.json()}')
            return None
        return float(result_dict['asks'][0][0])

    async def get_symbol(self, contract_address: str):
        return await self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=Client.default_abi
        ).functions.symbol().call()

    async def send_token(self, contract_address: str, to: str, amount: int):
        contract = self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=Client.default_abi
        )
        return self.send_transaction(
            to=contract_address,
            data=contract.encodeABI('transfer',
                                    args=(
                                        to,
                                        amount
                                    ))
        )
