import hashlib
import os
import subprocess

from pwn import remote

SECCON_HOST = os.getenv("SECCON_HOST", "localhost")
SECCON_PORT = os.getenv("SECCON_PORT", "31337")

r = remote(SECCON_HOST, SECCON_PORT, level="debug")
r.recv()
r.sendline(b"1")

r.recvuntil(b'sha256("')
preimage_prefix = r.recvuntil(b'"')[:-1]
r.recvuntil(b"start with ")
bits = int(r.recvuntil(b" "))
for i in range(0, 1 << 32):
    your_input = str(i).encode()
    preimage = preimage_prefix + your_input
    digest = hashlib.sha256(preimage).digest()
    digest_int = int.from_bytes(digest, "big")
    if digest_int < (1 << (256 - bits)):
        break
r.recvuntil(b"YOUR_INPUT = ")
r.sendline(your_input)

r.recvuntil(b"uuid:")
uuid = r.recvline().strip()
r.recvuntil(b"rpc endpoint:")
rpc_url = r.recvline().strip().decode().replace("tokyo-payload.seccon.games", SECCON_HOST)
r.recvuntil(b"private key:")
private_key = r.recvline().strip().decode()
r.recvuntil(b"setup contract:")
setup_address = r.recvline().strip().decode()
r.close()

subprocess.run(
    [
        "forge",
        "script",
        "TokyoPayloadScript",
        "--sig",
        "run(address)",
        setup_address,
        "--broadcast",
        "--private-key",
        private_key,
        "--rpc-url",
        rpc_url,
    ]
)

r = remote(SECCON_HOST, SECCON_PORT, level="debug")
r.recv()
r.sendline(b"3")
r.recvuntil(b"uuid please: ")
r.sendline(uuid)
r.recvuntil(b"Here's the flag: \n")
flag = r.recvline().strip()
print(flag)
