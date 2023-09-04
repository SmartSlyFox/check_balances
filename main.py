import asyncio
from asyncio import sleep
from time import time
from web3 import AsyncWeb3
from async_client import Client
from data.config import WALLETS, rpc

print("=================================================================================================")


async def out(private_key, number):
    while True:
        client = Client(private_key=private_key, rpc=rpc)
        chain_id = await client.w3.eth.chain_id
        connected = await client.w3.is_connected()
        balance = await client.w3.eth.get_balance(client.address)  # balance in wei
        ether_balance = AsyncWeb3.from_wei(balance, 'ether')  # converting in ether

        print(f"Wallet {number}")
        print(f"Connecting to network {chain_id} : {connected}")
        print(f'Balance in ETH {ether_balance}')
        print("=================================================================================================")
        # await sleep(1)

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
