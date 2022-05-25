# credict-chainlink-spring22

Credibly predict oracles. [Project for Chainlink Hackathon Spring 2022](https://devpost.com/software/credible-prediction-record)

## Getting started

### Interact with existing contract instances

#### PredictionRecorder: stores prediction data in a trust-worthy way

-   [Video guide](https://youtu.be/hzypdx23U4k)
-   [Example PredictionRecorder for ETH/USD on Rinkeby](https://rinkeby.etherscan.io/address/0xe92232688a4ee9b0a0a0d2ce596e8bed152097d7)

#### InvitationalBet: a showcase application that reads prediction data and oracle rounds to bet

-   [Video guide](https://youtu.be/hzypdx23U4k?t=197)
-   [Example InvitationalBet for the above PredictionRecorder](https://rinkeby.etherscan.io/address/0x15315533971A70945857daf7BE53727CcC057C9D)


This work is mostly a single Solidity file: [`PredictionRecorder.sol`](truffle/contracts/PredictionRecorder.sol). You can deploy two contracts and verify their source codes. Then you can interact with the deployed contracts using any Web3 provider.

### Deploy and verify new instances

#### Dependencies

[`hdwallet-provider`](https://www.npmjs.com/package/@truffle/hdwallet-provider) is for authentication and [`truffle-plugin-verify`](https://github.com/rkalis/truffle-plugin-verify) is for verifying source codes that contain imports.

```
npm install @truffle/hdwallet-provider
npm install -D truffle-plugin-verify
```

#### Environment variables

In the [`truffle` folder](truffle/) you need two files to **locally** configure authentication credentials.

-   create a `.env` file to hold `INFURA_PROJECT_ID` and `ETHERSCAN_API_KEY`.
-   create a `.secret` fild to hold mnenomics (space-separated words, typically 12 of them) that generate your HDWallet.

To deploy `PredictionRecorder` or `InvitationalBet`, modify the comments in [`migrations.js`](truffle/migrations/2_deploy_contracts.js). Then
```
truffle deploy --network rinkeby
truffle run verify <the-contract-you-deployed> --network rinkeby
```

### Optional Python API

Secure original predictions need encryption, decryption, and watermarks, which we suggest managing programmatically. For instance, you can consider taking a look at the [`python` folder](python/) to use `credict-py`. It takes care of RSA encryption and watermarks.
