var PredictionRecorder = artifacts.require("PredictionRecorder");
var InvitationalBet = artifacts.require("InvitationalBet");
module.exports = function(deployer) {
    //deployer.deploy(PredictionRecorder, "0x8A753747A1Fa494EC906cE90E9f37563A8AF630e");
    deployer.deploy(
        InvitationalBet,
        "0xE92232688A4EE9b0a0A0d2CE596E8bEd152097d7",
        ["0xEAEbD562C0e2A1ba7D8827616279020a979e977B", "0x84737E370BB2fB2A72D2Bef2E705b8C5A2A3f6Be", "0x85b63d4eD55f4E2BC0Bc8e3c0E7Ce58CFedE5Fe3"],
        1651982400,
        1651982100,
        1651983000,
        6,
    );
};
