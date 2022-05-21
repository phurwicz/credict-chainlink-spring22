"""
High-level API.
"""
import json
import time
import pandas as pd
from rich.console import Console
from rich.prompt import Confirm
from .encryption import RSA
from .watermark import AddressBasedWatermarker


class PredictionHandler:
    PREDICTION_SCHEMA = (
        "target_oracle",
        "target_time",
        "creation_time",
        "predicted_value",
        "is_decrypted",
        "prediction_address",
        "prediction_author",
        "prediction_comment",
    )
    
    def __init__(
        self,
        sender_address,
        contract_dict,
        target_digits=12,
    ):
        self.logger = Console()
        self.sender_address = sender_address
        self.contract_dict = contract_dict
        self.target_digits = target_digits
        self.setup_watermark()
        self.records_to_decrypt = []
    
    @classmethod
    def from_json(cls, path):
        with open(path, "r") as f:
            data_dict = json.load(f)
        handler = cls(
            data_dict["sender_address"],
            data_dict["contract_dict"],
            data_dict["target_digits"],
        )
        
        handler.setup_rsa(**data_dict["rsa_config"])
        handler.records_to_decrypt = data_dict["records_to_decrypt"]
        return handler
        
    @staticmethod
    def json_path_static(sender_address, contract_address):
        return f"{sender_address}_{contract_address}.json"
        
    def json_path_auto(self):
        return PredictionHandler.json_path_static(
            self.sender_address,
            self.contract_dict['address'],
        )
        
    def to_json_auto(self):
        self.to_json(self.json_path_auto())
        
    def to_json(self, path):
        assert hasattr(self, "rsa"), "missing RSA setup"
        
        data_dict = {
            "sender_address": self.sender_address,
            "contract_dict": self.contract_dict,
            "target_digits": self.target_digits,
            "rsa_config": self.rsa.describe(),
            "records_to_decrypt": self.records_to_decrypt,
        }
        
        with open(path, "w") as f:
            json.dump(data_dict, f)
        
    def connect(self, web3_provider):
        self.w3 = web3_provider
        self.contract = self.w3.eth.contract(
            abi=self.contract_dict["abi"],
            address=self.contract_dict["address"],
        )
        
    def setup_rsa(self, n=None, e=None, d=None):
        if n and e and d:
            self.logger.print("Loading preset RSA.")
            self.rsa = RSA(n, e, d)
        else:
            assert n is None and e is None and d is None
            self.logger.print("Creating RSA from scratch.")
            self.rsa = RSA.given_digits(self.target_digits)
            
    def setup_watermark(self, num_verifications=20):
        self.watermarker = AddressBasedWatermarker(self.sender_address)
        for _ in range(num_verifications):
            _watermark = self.watermarker.create(self.target_digits)
            assert self.watermarker.verify(_watermark)
        
    def make_prediction(self, txn_func, target_time, value, author="", comment=""):
        assert target_time > time.time(), f"invalid target time {target_time}"
        value_str = str(value)
        watermark_len = self.target_digits - 1 - len(value_str)
        assert watermark_len >= 5, f"available watermark length is too low for {value}"
        watermark = self.watermarker.create(watermark_len)
        
        marked_value = int(f"{watermark}0{value}")
        predicted_value = self.rsa.encrypt(marked_value)
        
        self.logger.print("Please review the prediction to be sent:")
        self.logger.print(target_time, predicted_value, author, comment)
        txn_flag = Confirm.ask("Proceed to transaction?")
        
        if txn_flag:
            call = self.contract.functions.makePrediction(
                target_time,
                predicted_value,
                author,
                comment,
            )
            
            txn_hash = txn_func(call)
            txn_receipt = self.w3.eth.waitForTransactionReceipt(txn_hash)
            
            if txn_receipt["status"] == 1:
                decryption_info = {
                    "target_time": target_time,
                    "predicted_value": predicted_value,
                    "rsa": self.rsa.describe(),
                }
                self.records_to_decrypt.append(decryption_info)
                json_root = f"{self.sender_address}_{self.contract_dict['address']}"
                self.to_json_auto()
            return txn_receipt
        
        return None

    def view_prediction(self):
        pred_list = self.contract.functions.viewPrediction(self.sender_address).call()
        dict_list = []
        schema = self.__class__.PREDICTION_SCHEMA
        for _pred in pred_list:
            _data_dict = {_k: _v for _k, _v in zip(schema, _pred)}
            dict_list.append(_data_dict)
        
        return dict_list
    
    @staticmethod
    def subroutine_match_prediction(chain_pred, local_record):
        for _field in ["target_time", "predicted_value"]:
            assert chain_pred[_field] == local_record[_field], f"{_field} mismatch: {chain_pred[_field]} (chain) vs. {local_record[_field]} (local)"
            
    def subroutine_find_decryption_param(self, pred_dict_list):
        """
        Identify the next decryption parameters and all predictions that use it.
        """
        # the first still-encrypted pred record should match the first local record
        local_first = self.records_to_decrypt[0]
        pred_index, rsa_dict = None, None
        for _index, _pred in enumerate(pred_dict_list):
            assert isinstance(_pred["is_decrypted"], bool)
            if not _pred["is_decrypted"]:
                PredictionHandler.subroutine_match_prediction(_pred, local_first)
                pred_index = _index
                rsa_dict = local_first["rsa"]
                break
        
        if pred_index is None:
            self.logger.print("Found no prediction to decrypt.")
            return None, None
        
        rsa_streak_len = 0
        for _record in self.records_to_decrypt:
            if _record["rsa"] != rsa_dict:
                break
            rsa_streak_len += 1
        
        # pair with chain records to get sanity check and decryption preview
        pred_slice = pred_dict_list[pred_index:(pred_index+rsa_streak_len)]
        record_slice = self.records_to_decrypt[:rsa_streak_len]
        rsa_streak_time_thresh = 0
        current_time = int(time.time())
        rsa_obj = RSA(rsa_dict["n"], rsa_dict["e"], rsa_dict["d"])
        
        for _pred, _record in zip(pred_slice, record_slice):
            # these fields must match between chain and local
            PredictionHandler.subroutine_match_prediction(_pred, _record)
            
            # add fields for preview
            _decrypted_value = rsa_obj.decrypt(_pred["predicted_value"])
            _watermark, _value = self.watermarker.extract(_decrypted_value)
            _pred["watermark"] = _watermark
            _pred["decrypted_value"] = _value
            _pred["copyable"] = _pred["target_time"] > current_time
            
            # creation times are expected to monotonically increase
            assert _pred["creation_time"] >= rsa_streak_time_thresh, "creation time misorder"
            rsa_streak_time_thresh = _pred["creation_time"]
        
        preview_df = pd.DataFrame(pred_slice)
        decrypt_params = (rsa_dict["d"], rsa_dict["n"], rsa_streak_time_thresh)
        return decrypt_params, preview_df
        
        
    def decrypt_prediction(self, txn_func):
        pred_dict_list = self.view_prediction()
        params, preview_df = self.subroutine_find_decryption_param(pred_dict_list)
        if params is None:
            return None
        
        # match using lookup to determine the creation time threshold
        call = self.contract.functions.decryptPrediction(*params)
        
        self.logger.print("Please review the predictions to be decrypted:")
        self.logger.print(preview_df)
        self.logger.print("Please review the decryption parameters:")
        self.logger.print(params)
        txn_flag = Confirm.ask("Proceed to transaction?")
        
        if txn_flag:
            txn_hash = txn_func(call)
            txn_receipt = self.w3.eth.waitForTransactionReceipt(txn_hash)
        
            if txn_receipt["status"] == 1:
                for _ in range(preview_df.shape[0]):
                    self.records_to_decrypt.pop(0)
                
                if not self.records_to_decrypt:
                    self.setup_rsa()
                    
                self.to_json_auto()
            return txn_receipt
        
        return None
