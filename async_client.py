from typing import Optional
from web3 import AsyncWeb3, AsyncHTTPProvider
from data.config import TOKEN_ABI
from utils import read_json


class Client:
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

    async def check_balance_interface(self, token_address, min_value) -> bool:
        print(f'{self.address} | check balance {await self.get_symbol(token_address)} token')
        balance = await self.balance_of(contract_address=token_address)
        decimal = await self.get_decimals(contract_address=token_address)
        if balance < min_value * 10 ** decimal:
            print(
                f'{self.address} | balance {await self.get_symbol(token_address)} token lower then {min_value} {await self.get_symbol(token_address)}')
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
                print(f'{self.address} | Transaction success: {tx_hash.hex()}')
                return True
            else:
                print(f'{self.address} | Transaction false {data["transactionHash"].hex()}')
                return False
        except Exception as err:
            print(f'{self.address} | unexpected error in <verif_tx> : {err}')
            return False

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
