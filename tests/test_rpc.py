from web3 import Web3
from config import RPC_URL


w3 = Web3(Web3.HTTPProvider(RPC_URL))

print("Connected:", w3.is_connected())

if w3.is_connected():
    print("Chain ID:", w3.eth.chain_id)
    print("Latest block:", w3.eth.block_number)