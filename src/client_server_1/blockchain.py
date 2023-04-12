import time
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from urllib.parse import urlparse

# Building a Blockchain
class Blockchain:

    # constructor
    def __init__(self):
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0' , sender = 'N.A' , receiver = 'N.A' , file_hash = 'N.A') ##########
        self.nodes = set()
        self.nodes.add("127.0.0.1:5111")
    
    # creates new block and appends it to chain list
    def create_block(self, proof, previous_hash, sender, receiver, file_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(time.strftime("%d %B %Y , %I:%M:%S %p", time.localtime())),  # d-date, B-Month, Y-Year ,I-Hours in 12hr format, M-Minutes, S-secnods, p-A.M or P.M
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'sender': sender,
                 'receiver':receiver, 
                 'shared_files': file_hash}
        self.chain.append(block)
        return block

    # returns previous block from chain
    def get_previous_block(self):
        return self.chain[-1]

    # calculates proof(nonce). for greater strength increase condition string size
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            # currently set string size small for demo purpose
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    # hash the previous block by hashing its json
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    # verify
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        # verify each block in chain
        while block_index < len(chain):
            block = chain[block_index]
            # if previous_hash in give chain is different from calculated hash then its invalid
            if block['previous_hash'] != self.hash(previous_block):
                return False
            # if given proof is invalid proof then chain is invalid
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    # method to add new block in blockchain
    def add_file(self, sender, receiver, file_hash):
        previous_block = self.get_previous_block()
        index = previous_block['index'] + 1
        previous_proof = previous_block['proof']
        proof = self.proof_of_work(previous_proof)
        previous_hash = self.hash(previous_block)
        self.create_block(proof, previous_hash, sender, receiver, file_hash)
        return index
    
    # sync chain from network
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        print(network)
        # go through each node and get there chain
        # check if chain is valid and keep track of longest chain
        # set own chain to longest chain
        for node in network:
            print(f'http://{node}/get_chain')
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False