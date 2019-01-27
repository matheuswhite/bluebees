
class Message:

    def __init__(self, opcode: bytes, parameters: bytes):
        self.opcode = opcode
        self.parameters = parameters

class Model:

    def __init__(self, model_id: int):
        self.model_id = model_id
