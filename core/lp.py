V2_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
        ],
        "name": "getPair",
        "outputs": [
            {"internalType": "address", "name": "pair", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
            {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
            {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
]