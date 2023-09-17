// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.21;

import {Script} from "forge-std/Script.sol";
import {Setup, TokyoPayload} from "./challenge/Setup.sol";
import {exploit} from "./Exploit.sol";

contract TokyoPayloadScript is Script {
    function run(address setupAddr) public {
        vm.startBroadcast();
        exploit(setupAddr);
        vm.stopBroadcast();
        require(Setup(setupAddr).isSolved());
    }
}
