# Plunger

Tool helping to deal with Ethereum transactions stuck in the pool.

<https://chat.makerdao.com/channel/keeper>


## Rationale

Due to periodic Ethereum network congestion, transactions can easily get stuck in the
transaction pool for many hours if not days. _plunger_ is a tool that helps to deal
with such situations by either overriding them with zero-valued transactions with
higher gas price, or just waiting for them to clear themselves. It also allows you
to list pending transactions for manual inspection.

_plunger_ has been created as part of development of the Maker Keeper Framework.
It is essential to run each keeper from an individual address, which does not
have any pending transactions. That's why before starting each keeper, doing
a `plunger --wait 0x.....` if recommended.

If you want to discuss this tool, the best place will be the _#keeper_ channel
in Maker RocketChat, linked above.


## Installation

This project uses *Python 3.6.2*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/reverendus/plunger.git
pip3 install -r requirements.txt
```

### Known macOS issues

In order for the requirements to install correctly on _macOS_, please install
`openssl`, `libtool` and `pkg-config` using [Homebrew](https://brew.sh/):
```
brew install openssl libtool pkg-config
```

and set the `LDFLAGS` environment variable before you run `pip3 install -r requirements.txt`:
```
export LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" 
```


## Listing pending transactions

**TODO This feature is not implemented yet!**

```bash
bin/plunger --list 0x0101010101010101010101010101010101010101
```


## Waiting for pending transactions to clear

If you want _plunger_ to just wait for the pending transactions from the specified address
to get processed by the network (i.e. to get mined), run it with the `--wait` argument:

```bash
bin/plunger --wait 0x0101010101010101010101010101010101010101
```

This is a completely passive mode i.e. no Ethereum transactions get sent by _plunger_
if called with `--wait`.

_Plunger_ will not terminate until all pending transactions get mined. If it for some exceptional
reason (the Ethereum node going down or some other network connectivity issues) terminates earlier
than that, it will return a non-zero return code.


## Overriding pending transactions

**TODO This feature is not implemented yet!**

If you want _plunger_ to try to override all pending transactions with a zero Wei ether transfer
but with gas cost higher than the original, run it with the `--override-with-zero-txs` argument:

```bash
bin/plunger --override-with-zero-txs 0x0101010101010101010101010101010101010101
```

_Plunger_ will send replacement transactions immediately, then it will start monitoring the
network and will not terminate until all pending transactions or their replacements get mined.
**Due to the nature of the Ethereum network, there is no guarantee which transactions will
actually get executed.** It is possible that some of the original stuck ones will actually
get through. You can also get a mix of old and new ones being mined when there is more than
one transaction pending.

If for some exceptional reason (the Ethereum node going down or some other network
connectivity issues) _plunger_ terminates before all pending transactions from the specified
address get mined, it will return a non-zero return code.

The account specified has to be unlocked for _plunger_ to be able to sign and send replacement
transactions. If it's unable to do so, it will terminate immediately with a non-zero return code.

### Gas price used

By default, _plunger_ will use the default gas price suggested by the Ethereum node it is
connected to. If that gas price is lower than the one the pending transactions have used,
_pluger_ will increase it by 1 Wei.

**TODO This feature is not implemented yet!** In the future it will be possible to specify
a custom gas price or use a service like _ethgasstation_.

### Zero Wei ether transfer transaction used

**TODO This subsection will describe transaction that plunger overrides with**


## License

See [COPYING](https://github.com/reverendus/plunger/blob/master/COPYING) file.
