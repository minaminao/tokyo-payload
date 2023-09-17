# Tokyo Payload

**Tokyo Payload** is an EVM Jump-Oriented Programming puzzle I created for SECCON CTF 2023 Quals.

This repo includes:
- `build`: the source codes of the challenge server. based on https://github.com/Zellic/example-ctf-challenge
- `files`: the distributed files for players
- `solver`: the source code of the solver

## The distributed files

TokyoPayload.sol:
```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.21;

contract TokyoPayload {
    bool public solved;
    uint256 public gasLimit;

    function tokyoPayload(uint256 x, uint256 y) public {
        require(x >= 0x40);
        resetGasLimit();
        assembly {
            calldatacopy(x, 0, calldatasize())
        }
        function()[] memory funcs;
        uint256 z = y;
        funcs[z]();
    }

    function load(uint256 i) public pure returns (uint256 a, uint256 b, uint256 c) {
        assembly {
            a := calldataload(i)
            b := calldataload(add(i, 0x20))
            c := calldataload(add(i, 0x40))
        }
    }

    function createArray(uint256 length) public pure returns (uint256[] memory) {
        return new uint256[](length);
    }

    function resetGasLimit() public {
        uint256[] memory arr;
        gasLimit = arr.length;
    }

    function delegatecall(address addr) public {
        require(msg.sender == address(0xCAFE));
        (bool success,) = addr.delegatecall{gas: gasLimit & 0xFFFF}("");
        require(success);
    }
}
```

Setup.sol:
```solidity
// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.21;

import {TokyoPayload} from "./TokyoPayload.sol";

contract Setup {
    TokyoPayload public tokyoPayload;

    constructor() {
        tokyoPayload = new TokyoPayload();
    }

    function isSolved() public view returns (bool) {
        return tokyoPayload.solved();
    }
}
```

## Launch a challenge server

```
cd build
docker compose up
```

## Access the challenge server

```
nc localhost 31337
```

Good luck!

---

## Run the author's solver

Local:
```
cd solver
docker run -e SECCON_HOST=localhost -e SECCON_PORT=31337 --network=host (docker build -q .)
```

Remote:
```
cd solver
docker run -e SECCON_HOST=tokyo-payload.seccon.games -e SECCON_PORT=31337 (docker build -q .)
```
