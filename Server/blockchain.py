# blockchain.py
import hashlib
import time

class Block:
    def __init__(self, index, previous_hash, timestamp, data, hash):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.hash = hash

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block(0, "0", 0, "Genesis Block", "0")

    def add_block(self, data):
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), previous_block.hash, time.time(), data, self.calculate_hash(previous_block.hash, data))
        self.chain.append(new_block)

    def calculate_hash(self, previous_hash, data):
        return hashlib.sha256(f"{previous_hash}{data}".encode()).hexdigest()

    def receive(self, data):
        self.add_block(data)
