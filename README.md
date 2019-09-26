[![Build Status](https://travis-ci.org/onokatio/plasma-mvp.svg?branch=master)](https://travis-ci.org/onokatio/plasma-mvp)

This is a fork from plasma-mvp for hierarchical plasma.

# Build Environment

```
$ pyenv install 3.6.9
$ python3 -m venv venv
$ source venv/bin/activate
```


# Port

Child Chain operator: 8546
Grand Child Chain operator: 8547

# directory structure

`contract_data` : ABI
`plasma_core/` : plasma data structure library. define block and transaction.
`plasma/root_chain` : Solidity contract
`plasma/child_chain` : Child chain operator. Run as jsonrpc server. It can also makes transaction.
`plasma/client` : Python library to call `plasma/child_chain` server.
`plasma/cli` : command line tool. It just use client library.

# UTXO contract state

```
{[
	{"root": 0x123456789...123456789 , "timestamp": 1569312178},
}}
```

# Notice!
This is an old research repo. No active work is being done here. Efforts in the direction of production-ready MVP plasma chain (MoreVP, ERC20, audits) are in https://github.com/omisego/plasma-contracts.

# Plasma MVP

We're implementing [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426). This repository represents a work in progress and will undergo large-scale modifications as requirements change.

## Overview

Plasma MVP is split into four main parts: `root_chain`, `child_chain`, `client`, and `cli`. Below is an overview of each sub-project.

### root_chain

`root_chain` represents the Plasma contract to be deployed to the root blockchain. In our case, this contract is written in Solidity and is designed to be deployed to Ethereum. `root_chain` also includes a compilation/deployment script.

`RootChain.sol` is based off of the Plasma design specified in [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426). Currently, this contract allows a single authority to publish child chain blocks to the root chain. This is *not* a permanent design and is intended to simplify development of more critical components in the short term.

### child_chain

`child_chain` is a Python implementation of a Plasma MVP child chain client. It's useful to think of `child_chain` as analogous to [Parity](https://www.parity.io) or [Geth](https://geth.ethereum.org). This component manages a store of `Blocks` and `Transactions` that are updated when events are fired in the root contract.

`child_chain` also contains an RPC server that enables client interactions. By default, this server runs on port `8546`.

### client

`client` is a simple Python wrapper of the RPC API exposed by `child_chain`, similar to `Web3.py` for Ethereum. You can use this client to write Python applications that interact with this Plasma chain.

### cli

`cli` is a simple Python application that uses `client` to interact with `child_chain`, via the command line. A detailed documentation of `cli` is available [here](#cli-documentation).

## Getting Started

### Dependencies

This project has a few pre-installation dependencies.

#### [Solidity ^0.5.0](https://solidity.readthedocs.io/en/latest/installing-solidity.html)

#### [Python 3.2+](https://www.python.org/downloads/)

#### [Ganache CLI 6.1.8+](https://github.com/trufflesuite/ganache-cli)

## CLI Example

Let's play around a bit:

### 1. Deploy the root chain contract and start the child chain as per [Starting Plasma](#starting-plasma).
```
$ make clean
$ make
$ ganache-cli -m=plasma_mvp
$ make root-chain
$ python ./plasma/child_chain/server.py
```

### 2. Start by depositing:
```
# deposit 100 wei to child chain.
# it can be used in child chain at `1 0 0`(blknum1 txindex1 oindex1)
python plasma/cli/cli.py deposit 100 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7
```

blknum1, txindex1, oindex1 is a point of UTXO. blknum is block number, txindex is transaction number, and oindex is output number of transaction.
There are two point (such as blknum1 blknum2) and two newowner. So we can use two input and two outpu maximam.

### 3. Create UTXO contract and use

#### 3-1. deposit 100 and create UTXO contract

0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 is contract address.
Only operator can make contract address.

```
python plasma/cli/cli.py sendtx 1 0 0 0 0 0 0x0 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 100 0x0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 0x01 '{[]}'
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has 100wei at first.
Then, it send 100wei to 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26.


UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 
UTXO that 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 has : 2-0-0(100wei)

a-b-c means blknum-txindex-oindex.

#### 3-2. state update

```
python plasma/cli/cli.py --gc --gcnum 1000 submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 
UTXO that 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 has : 5-0-0(100wei)
(child chain doesn't know grandchild chain each address's amount. only knows total amount is 100wei)

#### 3-3. exit grandchild chain to child chain

```
```

### 4. exit 10wei at 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 to root chain

```
python plasma/cli/cli.py sendtx 5 0 0 0 0 0 0x0 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 40 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 10 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 0x01 '{[{"root": 0x1 , "timestamp": 1569312178},{"root": 0x1 , "timestamp": 1569312179},]}'
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 2-0-0(50wei) 6-0-1(10wei)
UTXO that 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 has : 6-0-0(40wei)

4.  Submit the block:
```
python ./plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

5. Withdraw the original deposit (this is a double spend!):

```
python ./plasma/cli/cli.py withdrawdeposit 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 1 60
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 
UTXO that 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 has : 6-0-0(40wei)

Note: The functionality to challenge double spends from the cli is still being worked on.
