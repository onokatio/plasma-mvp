[![Build Status](https://travis-ci.org/onokatio/plasma-mvp.svg?branch=master)](https://travis-ci.org/onokatio/plasma-mvp)

This is a fork from plasma-mvp for hierarchical plasma.

# Plasma on Plasma

## Port

Child Chain operator: 8546
Grand Child Chain operator: 8547

## directory structure

`contract_data` : ABI that exported by solc
`plasma_core/` : plasma data structure library. define block and transaction.
`plasma_core/constants.py` : Account public key and private key list. Use these for <key> argument.
`plasma/root_chain` : Solidity contract
`plasma/child_chain` : Child chain operator. Run as jsonrpc server. It can also makes transaction.
`plasma/grandchild_chain` : Grand Child chain operator. Run as jsonrpc server. It can also makes transaction.
`plasma/client` : Python library to call jsonrpc of `plasma/child_chain` server.
`plasma/cli` : command line tool. It just use client library.

## transaction specifications

### tx.contractflag

`0x00`: normal transaction
`0x01`: UTXO contract transaction

### tx.state

defined as json string.

```
{[
	{"root": 0x123456789...123456789 , "timestamp": 1569312178},
	{"root": 0x123456789...123456790 , "timestamp": 1569312179},
}}
```

## Getting Started

### Dependencies

This project has a few pre-installation dependencies.

#### [Solidity ^0.5.0](https://solidity.readthedocs.io/en/latest/installing-solidity.html)

#### [Python 3.2+](https://www.python.org/downloads/)

#### [Ganache CLI 6.1.8+](https://github.com/trufflesuite/ganache-cli)

## CLI Example

Let's play around a bit:

### 1. Deploy the root chain contract and start the child chain , grand child chain.

```
$ pyenv install 3.6.9
$ python3 -m venv venv
$ source venv/bin/activate
$ make clean
$ make
$ ganache-cli -m=plasma_mvp
$ make root-chain
$ python ./plasma/child_chain/server.py
$ python ./plasma/grandchild_chain/server.py
```


### Start by deposit:

Deposit 100 wei to child chain.
It can be used in child chain at `1 0 0`(blknum1 txindex1 oindex1)
blknum1, txindex1, oindex1 is a point of UTXO. blknum is block number, txindex is transaction number, and oindex is output number of transaction.
There are two point (such as blknum1 blknum2) and two newowner. So we can use two input and two outpu maximam.

```
python plasma/cli/cli.py deposit 100 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26
```


### 3. Create UTXO contract and use

#### 3-0. deposit 0 and create UTXO contract

0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 is contract address.
Only operator can make contract address.


```
python plasma/cli/cli.py deposit 0 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7
python plasma/cli/cli.py sendtx 2 0 0 0 0 0 0x0 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 0 0x0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 0x01 '{[]}'
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

#### 3-1. deposit 100 to UTXO contract

deposit 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 to 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7
```
python plasma/cli/cli.py sendtx 1 0 0 0 0 0 0x0 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 100 0x0 0 b937b2c6a606edf1a4d671485f0fa61dcc5102e1ebca392f5a8140b23a8ac04f 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304

python plasma/cli/cli.py --gc --gcnum 1000 apply_deposit_utxo 2000 0 0
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 1000-0-0(100wei)

a-b-c means blknum-txindex-oindex.

#### 3-2. state update

```
# send 100wei from 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 to 0xda20A48913f9031337a5e32325F743e8536860e2
python plasma/cli/cli.py --gc sendtx 1 0 0 0 0 0 0x0 0xda20A48913f9031337a5e32325F743e8536860e2 100 0x0 0 b937b2c6a606edf1a4d671485f0fa61dcc5102e1ebca392f5a8140b23a8ac04f 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304

python plasma/cli/cli.py --gc --gcnum 1000 submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 2000-0-0(100wei)
(child chain doesn't know grandchild chain each address's amount. only knows total amount is 100wei)

#### 3-3. exit grandchild chain to child chain

withdraw 0xda20A48913f9031337a5e32325F743e8536860e2's 100wei

```
python ./plasma/cli/cli.py --gc --gcnum 2000 withdraw 1000 0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304 0xda20A48913f9031337a5e32325F743e8536860e2
python plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### 4. send inside child chain.

```
python ./plasma/cli/cli.py sendtx 3000 0 1 0 0 0 0x0 0xda20A48913f9031337a5e32325F743e8536860e2 100 0x0 0 999ba3f77899ba4802af5109221c64a9238a6772718f287a8bd3ca3d1b68187f 999ba3f77899ba4802af5109221c64a9238a6772718f287a8bd3ca3d1b68187f
python ./plasma/cli/cli.py submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

# Withdraw the original deposit (this is a double spend!):

```
python ./plasma/cli/cli.py withdrawdeposit 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 1 60
python ./plasma/cli/cli.py withdraw 4000 0 0 999ba3f77899ba4802af5109221c64a9238a6772718f287a8bd3ca3d1b68187f
```

UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 
UTXO that 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 has : 6-0-0(40wei)

Note: The functionality to challenge double spends from the cli is still being worked on.
