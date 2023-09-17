// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.21;

import {Test} from "forge-std/Test.sol";
import {Setup, TokyoPayload} from "./challenge/Setup.sol";
import {exploit} from "./Exploit.sol";

contract TokyoPayloadTest is Test {
    Setup setup;
    address playerAddr;

    function setUp() public {
        setup = new Setup();
        playerAddr = makeAddr("player");
    }

    function test() public {
        vm.startPrank(playerAddr, playerAddr);
        exploit(address(setup));
        vm.stopPrank();
        assertTrue(setup.isSolved());
    }
}
