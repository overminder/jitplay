
class OperationError(Exception):
    def __init__(self, w_err):
        self.w_err = w_err

    def match(self, w_errclass):
        return isinstance(self.w_err, w_errclass)

    def unwrap(self):
        return self.w_err
