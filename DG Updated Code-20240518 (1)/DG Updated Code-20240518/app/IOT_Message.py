from Imports import *

class MessageValue(object):
    def __init__(self, DisplayName: str, Address: str, Value: str):
        self.DisplayName = DisplayName
        self.Address = Address
        self.Value = Value
class Data(object):
    def __init__(self, CorrelationId: str, SourceTimestamp: str, Values: List[MessageValue]):
        self.CorrelationId = CorrelationId
        self.SourceTimestamp = SourceTimestamp
        self.Values = Values

class Content(object):
    def __init__(self, HwID: str, Data: List[Data]):
        self.HwID = HwID
        self.Data = Data

class IOTMessage(object):
    def __init__(self,PublishTimestamp: str,Content: List[Content]):
        self.PublishTimestamp = PublishTimestamp
        self.Content = Content