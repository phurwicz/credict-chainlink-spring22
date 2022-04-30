// SPDX-License-Identifier: MIT
pragma solidity >=0.7.0;

contract PredictionRecorder {

    struct Prediction {
        address targetOracle;
        uint targetTime;
        uint creationTime;
        int predictedValue;
        bool isDecrypted;
        address predictionAddress;
        string predictionAuthor;
        string predictionComment;
    }

    address private oracleAddress;
    mapping (address => Prediction[]) private predictions;
    mapping (address => uint) private decryptIndices;
    mapping (address => uint) private numDecryptionBatches;

    constructor(address _oracleAddress) {
        oracleAddress = _oracleAddress;
    }

    /**
     * Make a prediction and keep its record in this contract.
     * The prediction must be RSA encrypted, i.e. c = (m ** e) % n.
     * See: https://en.wikipedia.org/wiki/RSA_(cryptosystem)#Operation
     * If predicting a negative integer, the negative sign is ignored during RSA.
     */
    function makePrediction(
        uint _targetTime,
        int _encryptedPredictedValue,
        string memory _predictionAuthor,
        string memory _predictionComment
    ) external {
        require(block.timestamp < _targetTime, "Cannot predict the past.");

        predictions[msg.sender].push(Prediction({
            targetOracle: oracleAddress,
            targetTime: _targetTime,
            creationTime: block.timestamp,
            predictedValue: _encryptedPredictedValue,
            isDecrypted: false,
            predictionAddress: msg.sender,
            predictionAuthor: _predictionAuthor,
            predictionComment: _predictionComment
        }));
    }

    function test() public pure {
        require(logarithmFloor(4, 2) == 2);
        require(logarithmFloor(99, 10) == 1);
        require(logarithmFloor(100, 10) == 2);
        require(logarithmFloor(1000000, 100) == 3);
        require(powerWithModulos(3, 1, 1, 7) == 3);
        require(powerWithModulos(3, 2, 3, 7) == 2);
        require(powerWithModulos(3, 3, 3, 7) == 6);
        require(powerWithModulos(3, 4, 3, 7) == 4);
        require(uintToDigits(1234)[3] == 4);
    }

    /**
     * Simple integer logarithm, taking the floor.
     */
    function logarithmFloor(uint number, uint base) public pure returns (uint) {
        require(base >= 2, "Base must be at least 2.");
        uint logValue = 0;
        while (number >= base) {
            number /= base;
            logValue++;
        }
        return logValue;
    }

    /**
     * Raise a number to some power while taking modulos.
     */
    function powerWithModulos(uint base, uint power, uint log2PowerUpper, uint modulos) public pure returns (uint) {
        require(2 ** log2PowerUpper >= power, "Invalid argument value log2PowerUpper");
        /* cache stores base, base**2, base**4, base**8, ... all with % modulos */
        uint[] memory cache = new uint[](log2PowerUpper);
        uint twoToK = 1;
        uint k = 0;
        base = base % modulos;
        uint burner = base;
        while (power >= twoToK) {
            cache[k] = burner;
            twoToK *= 2;
            k += 1;
            burner = (burner * burner) % modulos;
        }
        uint result = 1;
        while (power > 0) {
            while (power < twoToK) {
                twoToK /= 2;
                k -= 1;
            }
            result = (result * cache[k]) % modulos;
            power -= twoToK;
        }
        return result;
    }

    /**
     * Decrypt predictions so that they become publically readable, i.e. m = (c ** d) % n.
     * This exposes the existing encryption, so the sender must replace their off-chain RSA keys.
     * The option upToCreationTime allows changing keys without having to decrypt previous predictions immediately.
     */
    function decryptPrediction(
        uint d,
        uint n,
        uint upToCreationTime
    ) external returns (uint) {
        address sender = msg.sender;
        uint prevDecryptIndex = decryptIndices[sender];

        /* Pre-compute a near upper bound of log_2(d) for fixed array size */
        uint log2dUpper = logarithmFloor(d, 2) + 1;

        /* Predictions are naturally sorted by their creation time in ascending order */
        for (uint i = decryptIndices[sender]; i < predictions[sender].length; i++) {
            /* If beyond set creation time limit, stop */
            if (predictions[sender][i].creationTime > upToCreationTime) {break;}

            /* Decryption: m = (c ** d) % n with log(d) running time and log(d) memory */
            int sign = predictions[sender][i].predictedValue >= 0 ? int(1) : int(-1);
            uint c = uint(sign * predictions[sender][i].predictedValue);
            uint m = powerWithModulos(c, d, log2dUpper, n);

            /* Finalize struct attribute change */
            predictions[sender][i].predictedValue = sign * int(m);
            predictions[sender][i].isDecrypted = true;
            decryptIndices[sender]++;
        }

        /* If anything got decrypted, increment the batch count */
        if (prevDecryptIndex < decryptIndices[sender]) {numDecryptionBatches[sender]++;}

        return decryptIndices[sender];
    }

    /**
     * View all the predictions made by an address.
     */
    function viewPrediction(address _predictionAddress) public view returns (Prediction[] memory) {
        return predictions[_predictionAddress];
    }

    /**
     * View the address of the oracle for sanity check.
     */
    function viewOracle() public view returns (address) {
        return oracleAddress;
    }

    /**
     * Break a number into digits from left to right.
     */
    function uintToDigits(uint number) public pure returns (uint[] memory) {
        uint numDigits = 1;
        uint burnerVariable = number;
        while (burnerVariable >= 10) {
            numDigits += 1;
            burnerVariable /= 10;
        }

        uint[] memory digits = new uint[](numDigits);
        burnerVariable = number;
        for (uint i = 0; i < numDigits; i++) {
            digits[numDigits - 1 - i] = burnerVariable % 10;
            burnerVariable /= 10;
        }
        return digits;
    }

    /**
     * Compare a watermarked value with an address.
     * Return a success flag, a length measure, and the watermark value.
     */
    function extractWatermark(
        uint watermarkedValue,
        uint[] memory addressDigits
    ) public pure returns (bool, uint, uint) {
        uint[] memory valueDigits = uintToDigits(watermarkedValue);

        /* Initialize return values and processing pointer */
        bool watermarkFlag = true;
        uint watermarkLength = 0;
        uint watermarkValue = 0;
        uint watermarkPointer = 0;

        for (uint j = 0; j < valueDigits.length; j++) {
            /* Watermark normally terminates upon the first 0 encountered */
            if (valueDigits[j] == 0) {
                break;
            }

            /* The watermark must be a "substring" of the integer form of the prediction sender's address */
            while (addressDigits[watermarkPointer] != valueDigits[j]) {
                watermarkPointer++;
                /* If address digits are exhausted, then substring match fails */
                if (watermarkPointer >= addressDigits.length) {
                    watermarkFlag = false;
                    break;
                }
            }

            /* Watermark check has failed: stop */
            if (!watermarkFlag) {break;}

            /* Watermark check continues: shift existing digits to the left and add current digit */
            watermarkValue *= 10;
            watermarkValue += valueDigits[j];
            watermarkLength++;
        }
        return (watermarkFlag, watermarkLength, watermarkValue);
    }

    /**
     * Turn an address into uint form.
     */
    function addressToUint(address _address) public pure returns (uint) {
        return uint(uint160(_address));
    }

    /**
     * Count the number of distinct uints in a (portion of) a sorted array.
     */
    function countDistinctSortedUints(uint[] memory arr, uint maxIdx) public pure returns (uint) {
        if (maxIdx <= 1) {return maxIdx;}
        uint numDistincts = 1;
        for (uint i = 1; i < maxIdx; i++) {
            if (arr[i-1] == arr[i]) {numDistincts++;}
        }
        return numDistincts;
    }

    function quickSort(uint[] memory arr, int left, int right) internal pure {
        /* Initialize pointers */
        int i = left;
        int j = right;
        if (i==j) {return;}

        /* Partition: below pivot -> left; above pivot -> right */
        uint pivot = arr[uint((left + right) / 2)];
        while (i <= j) {
            while (arr[uint(i)] < pivot) {i++;}
            while (pivot < arr[uint(j)]) {j--;}
            if (i <= j) {
                (arr[uint(i)], arr[uint(j)]) = (arr[uint(j)], arr[uint(i)]);
                i++;
                j--;
            }
        }

        /* Divide and conquer */
        if (left < j) {quickSort(arr, left, j);}
        if (i < right) {quickSort(arr, i, right);}
    }

    /**
     * Analyze prediction records to measure its originality and trustworthiness.
     * Please find these statistics and suggested values in the return statement.
     */
    function analyzePredictionRecord(address _predictionAddress) public view returns (uint, uint, uint, uint, uint) {

        /* We use the integer form of the sender's address to produce (off-contract) and verify (in-contract) watermarks */
        Prediction[] memory storedPredictions = predictions[_predictionAddress];
        uint[] memory addressDigits = uintToDigits(addressToUint(_predictionAddress));

        /* For fewer local variables. [numDecryptedPredictions, numValidWatermarks, totalValidWatermarkLength] */
        uint[] memory intermediateStats = new uint[](3);
        uint[] memory validWatermarks = new uint[](storedPredictions.length);

        /* Decrypted predictions are always to the left of still-encrypted ones */
        for (uint i = 0; i < storedPredictions.length; i++) {
            /* If not yet decrypted, stop */
            if (!storedPredictions[i].isDecrypted) {break;}

            /* Take the predicted value without sign */
            (
                bool watermarkFlag,
                uint watermarkLength,
                uint watermarkValue
            ) = extractWatermark(
                uint(storedPredictions[i].predictedValue >= 0 ? storedPredictions[i].predictedValue : -storedPredictions[i].predictedValue),
                addressDigits
            );

            /* Update intermediate statistics */
            intermediateStats[0]++;
            if (watermarkFlag) {
                validWatermarks[intermediateStats[1]] = watermarkValue;
                intermediateStats[1]++;
                intermediateStats[2] += watermarkLength;
            }
        }

        /* Since dynamic mappings are not available, use sorting to count distinct watermarks */
        quickSort(validWatermarks, int(0), int(intermediateStats[1]));

        return (
            /* # decrypted predictions (no suggested value) */
            intermediateStats[0],
            /* # valid watermarks per 1000 predictions (as close to 1000 as possible) */
            (1000 * intermediateStats[1] / intermediateStats[0]),
            /* # distinct valid watermarks per 1000 predictions (as close to 1000 as possible) */
            (1000 * countDistinctSortedUints(validWatermarks, intermediateStats[1]) / intermediateStats[0]),
            /* average length of valid watermarks per prediction (8-15; too low is bad for security, too high can be costly) */
            intermediateStats[2] / intermediateStats[0],
            /* average predictions per decryption call (10-1000; too low is bad for trust, too high can be bad for security) */
            intermediateStats[0] / numDecryptionBatches[_predictionAddress]
        );
    }
}

