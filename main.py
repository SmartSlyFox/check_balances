import asyncio
from time import time
from web3 import AsyncWeb3
from async_client import Client
from data.config import WALLETS, rpc


async def out(private_key, number):
    client = Client(private_key=private_key, rpc=rpc)
    print(f"Wallet {number}")
    print(f"Connecting to network {await client.w3.eth.chain_id} : {await client.w3.is_connected()}")

    # balance in wei
    balance = await client.w3.eth.get_balance(client.address)

    # converting in ether
    ether_balance = AsyncWeb3.from_wei(balance, 'ether')
    print(f'Balance in ETH {ether_balance}')
    print("=================================================================================================")


async def main():
    tasks = []
    number = 0
    for private_key in WALLETS:
        number += 1

        task = asyncio.create_task(out(private_key, number))
        tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    time_start = time()
    asyncio.run(main())
    print(time() - time_start)
