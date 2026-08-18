# Hack The Box — RAuth (Reversing)

- **Author:** TheCyberGeek
- **Category:** Reversing
- **Difficulty:** Easy
- **Tools:** IDA Free, Python, Netcat

## Overview

`RAuth` looks like a basic password-bypass challenge: patch two conditional
jumps and the local binary accepts any password. That is only the first layer.
The local executable represents a development environment, while the flag is
served by an unmodified remote instance. To authenticate remotely, I had to
recover the real password.

The validation routine encrypts the supplied password with Salsa20 and compares
the result with a 32-byte value stored in two XMM constants. Extracting the
cipher state and correcting the constants' byte order gives everything needed
to recover the plaintext password:

```text
TheCrucialRustEngineering@2021;)
```

## Initial Analysis

The challenge provides a Linux executable and the address of a remote service.
I started by identifying and running the binary:

```bash
$ file rauth
rauth: ELF 64-bit LSB pie executable, x86-64, ...

$ chmod +x rauth
$ ./rauth
```

The program asks for a password and rejects arbitrary input. I loaded it into
IDA and followed the control flow from `main` into the authentication logic.

For interactive debugging in IDA, it is useful to start IDA from a terminal
whose standard input remains connected:

```bash
cat | ./ida64
```

## The Local Bypass

The authentication path contains two `JZ` instructions that prevent an invalid
password from reaching the success branch. Inverting them to `JNZ` makes the
patched binary report a successful login.

This is useful for confirming the control flow, but it does not complete the
challenge. The patched binary only simulates a development environment. The
remote service still runs the original validation logic, so it requires the
actual password rather than a patched success branch.

## Identifying Salsa20

Tracing the password-validation code leads to a Salsa20 routine. Salsa20 builds
an internal state from fixed constants, key material, a nonce, and a counter.
Its standard constant is the ASCII string:

```text
expand 32-byte k
```

Breaking as the state is constructed and examining the stack shows the constant
interleaved with the values used by this binary:

```text
expaef39f4f20e76e33bnd 3d4c270a32-byd25f4db338e81b10te k
```

Separating the state components reveals the key and nonce:

```text
Key:   ef39f4f20e76e33bd25f4db338e81b10
Nonce: d4c270a3
```

At this point, the remaining missing value is the encrypted reference password.

## Recovering the Ciphertext from XMM Constants

After encrypting the candidate password, the program compares the result with
data loaded through SSE instructions. The relevant 128-bit constants are:

```text
0F331CBA656F5D958D5A829A3B15F0505h
0F91BAD626FB63EE372EC9DC9312A4324h
```

IDA displays each constant as a large hexadecimal integer. On little-endian
x86, that integer representation is the reverse of the order in which its bytes
appear in memory. Splitting each value into byte pairs and reversing the pairs
produces:

```text
05 05 5F B1 A3 29 A8 D5 58 D9 F5 56 A6 CB 31 F3
24 43 2A 31 C9 9D EC 72 E3 3E B6 6F 62 AD 1B F9
```

The important distinction is that the **byte pairs** are reversed; the
characters inside each byte are not. For example, `F3` remains `F3`, rather
than becoming `3F`.

Combining both halves gives the complete 32-byte ciphertext:

```text
05055fb1a329a8d558d9f556a6cb31f3
24432a31c99dec72e33eb66f62ad1bf9
```

## Recovering the Password

I reproduced the binary's Salsa20 operation in Python using the extracted state
values and ciphertext. The recovered inputs were:

```python
key = bytes.fromhex("ef39f4f20e76e33bd25f4db338e81b10")
nonce = bytes.fromhex("d4c270a3")

ciphertext = bytes.fromhex(
    "05055fb1a329a8d558d9f556a6cb31f3"
    "24432a31c99dec72e33eb66f62ad1bf9"
)
```

The script must reproduce the same Salsa20 state layout used by the executable.
XORing the resulting keystream with the ciphertext recovers:

```text
TheCrucialRustEngineering@2021;)
```

Salsa20 is a stream cipher, so encryption and decryption are the same operation:
the data is XORed with the generated keystream. Once the key, nonce, and state
layout are known, no separate decryption primitive is necessary.

## Remote Authentication

With the real password recovered, connect to the supplied challenge service:

```bash
nc <host> <port>
```

Enter the password at the prompt:

```text
TheCrucialRustEngineering@2021;)
```

The remote instance accepts it and returns the flag.

## Why the Patch Is a Dead End

Patching the jumps changes the behavior of the local executable, not the data it
expects. The remote process cannot be modified, and it independently performs
the password check. The local bypass is therefore best treated as a hint: it
identifies the success path and exposes the fact that the challenge has separate
development and production environments.

The real solution is to reverse the comparison far enough to reconstruct its
inputs.

## Takeaways

1. **A local authentication bypass is not always the final objective.** Check
   whether a remote service requires the original credential.
2. **Recognizable cryptographic constants reveal intent.** The string
   `expand 32-byte k` is a strong Salsa20 signature.
3. **Inspect SIMD registers and constants.** Compilers frequently move fixed
   comparison data through XMM registers in 16-byte chunks.
4. **Account for representation versus memory order.** IDA's displayed integer
   and the bytes consumed by an x86 program may appear reversed.
5. **Dynamic analysis complements decompilation.** Breaking during cipher-state
   initialization makes runtime keys and nonces much easier to identify.
