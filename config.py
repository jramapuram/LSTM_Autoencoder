__author__ = 'jramapuram'

class config():
    def __init__(self, num_periods=128, num_test_periods=32, max_features=20000
                 , input_dim=512, hidden_dim=256
                 , activation='sigmoid', inner_activation='hard_sigmoid'
                 , initialization='glorot_uniform'
                 , optimizer='rmsprop', loss='mean_squared_error'
                 , truncate_gradient=-1, return_sequences=False):
        self.num_periods = num_periods
        self.num_test_periods = num_test_periods
        self.max_features = max_features
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.truncate_gradient = truncate_gradient
        self.return_sequences = return_sequences
        # options: 'glorot_normal', 'glorot_uniform', 'normal', 'he_normal', 'he_uniform'
        self.initialization = initialization
        self.inner_init = inner_activation
        self.activation = activation
        self.optimizer = optimizer
        self.loss = loss

    def get_config(self):
        return {"name":self.__class__.__name__,
            "input_dim":self.input_dim,
            "num_periods":self.num_periods,
            "num_test_periods":self.num_test_periods,
            "max_features":self.max_features,
            "hidden_dim":self.hidden_dim,
            "initialization":self.initialization,
            "inner_init":self.inner_init,
            "activation":self.activation,
            "optimizer":self.optimizer,
            "loss":self.loss,
            "truncate_gradient":self.truncate_gradient,
            "return_sequences":self.return_sequences}