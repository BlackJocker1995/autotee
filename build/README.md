# Intel SGX support.

## test environment
- Ubuntu 22.04 - 5.15.0-125-generic, VM, Intel 5222R;

- Ubuntu 20.04.1 - 5.15.0-124-generic, VM, AMD 3970X;

- Ubuntu 22.04 - 5.15.0-117-generic, VM, Ali cloud Z8 (Support SGX HW);

## Requirement
### Only compile
Compilation alone does not require device support for SGX; 
it merely requires the Rust SDK. 
Empirical evidence shows that it also works with AMD.

Install Rust:
```sh
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
```

It is necessary to install the corresponding Rust extension: https://github.com/fortanix/rust-sgx.

Example:
Switch to nightly
```sh
rustup default nightly
Add the toolchain
```

```sh
rustup target add x86_64-fortanix-unknown-sgx --toolchain nightly
Install the tools
```

```sh
cargo install fortanix-sgx-tools sgxs-tools
echo >> ~/.cargo/config -e '[target.x86_64-fortanix-unknown-sgx]\nrunner = "ftxsgx-runner-cargo"'
# Verify your SGX setup
sgx-detect

### Running Environment
To execute SGX programs, the device must support SGX and the appropriate drivers and SDK must be properly installed.

The installation process can be referenced at: https://help.aliyun.com/zh/ecs/user-guide/build-an-sgx-encrypted-computing-environment#f04d0e2f4efcg.

## Compile code

```
## Build
```sh
# Execute your enclave!
cargo new --bin hello-world
cd hello-world
cargo build --target x86_64-fortanix-unknown-sgx
```

## Run
```sh
# Execute your enclave!
cargo run --target x86_64-fortanix-unknown-sgx
```
