# credict-chainlink-spring22
Credict: credible prediction records. Project for Chainlink Hackathon Spring 2022.

## What
Participants predict oracle outcomes ->  predictions get stored on chain for future verification -> subject matter experts can prove themselves by predicting accurately

## Why
Anyone can claim to be a subject matter expert. Most people don’t have the time or the qualification to tell the true experts from the false ones. Oracles makes this easy — just pick the real-world truths that you care about and see who predicts it well. The prediction record is cryptographic truth.

## How
-   Which oracles to support?
    -   Any in the Chainlink network. We don’t pre-configure them, just use the identifier or address of the oracle. Could consider combinations of oracles.

-   What does a prediction look like?
    -   TargetOracle, TargetTime, PredictionValue, PredictionTime, PredictionAddress, Metadata (explanation of the prediction, alias of author, sponsor information, and more)

-   Where should predictions be submitted?
    -   On chain: potentially costly; may prevent spamming; definitely credible
    -   Layer 2 (?): much cheaper; may be susceptible to spam; need credibility

-   Who pays for the submission?
    -   To avoid spamming and draining, the party making the submission should pay the gas fee. To further discourage spamming, especially if PoS dramatically reduces gas fee, consider making the contract escrow a small number of some stablecoin till the prediction target value is revealed.

-   What is guaranteed after submitting a prediction?
    -   A NFT (certificate-like picture?) documenting this prediction and its metadata. So the worst deal that can happen is that you pay gas for a NFT certifying a terrible prediction.

-   Is there a reward for accurate predictions?
    -   Consider rolling average accuracy (windowed MAE?) because it protects against spamming and indicates consistency. Consider allowing sponsors for specific oracle predictions to produce NFT rewards (paying for the gas fee and getting sponsor name on the NFT; maybe optionally add FT rewards for even more incentives). FT rewards will be a function of the pool capped to some maximum. The contract itself can also mint a new FT.
    -   Might want to consider making it possible for sponsors to customize your evaluation metrics and pool.

-   Can prediction NFTs be traded?
    -   Good predictions signal subject matter expertise. So if those NFTs are tradable they should very clearly indicate who made the prediction. Traders will only buy those NFTs for collection purpose, not for claiming expertise that they don’t have.

-   Could you summarize the rules?
    -   Each oracle has its own reward pool and prediction records
    -   Predictors: select oracle, make prediction, pay gas, get single-prediction NFT, prove yourself
    -   Sponsors: select oracle, set rolling NFT gas donation, set FT donation, get exposure
