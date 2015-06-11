__author__ = 'jramapuram'

import os.path

from numpy import newaxis
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, AutoEncoder, Activation
from keras.layers.recurrent import LSTM, GRU
from keras.optimizers import SGD
from keras.utils.dot_utils import Grapher
from keras.regularizers import l2, zero
from convolutional import Convolution1D, MaxPooling1D


class TimeDistributedAutoEncoder:
    def __init__(self, conf):
        self.conf = conf
        self.model_dir = ''
        self.model_name = ''
        self.encoder_sizes = []
        self.decoder_sizes = []
        self.model = Sequential()

    @property
    def get_model_name(self):
        model_structure = 'weights_[%s]Enc_[%s]Dec_%dbatch_%depochs_%s_autoencoder.dat'
        model_name = model_structure % ('_'.join(str(e) for e in self.encoder_sizes)
                                        , '_'.join(str(d) for d in self.decoder_sizes)
                                        , int(self.conf['--batch_size'])
                                        , int(self.conf['--max_epochs'])
                                        , self.conf['--model_type'])
        model_dir = model_name.replace("weights_", "").replace(".dat", "")
        from data_manipulator import create_dir
        create_dir(model_dir)
        return model_dir, model_name

    def train_autoencoder(self, X_train, rotate_forward_count=-1):
        self.model.get_config(verbose=1)
        if self.conf['--optimizer'] == 'sgd':
            # customize SGD as the default keras constructor does not use momentum or nesterov
            sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
            self.model.compile(loss=self.conf['--loss'], optimizer=sgd)
        else:
            self.model.compile(loss=self.conf['--loss'], optimizer=self.conf['--optimizer'])

        self.model_dir, self.model_name = self.get_model_name
        model_exists = self.load_model(os.path.join(self.model_dir, self.model_name), self.model)

        if not model_exists:
            print 'training new model using %s loss function & %s optimizer...' \
                  % (self.conf['--loss'], self.conf['--optimizer'])

            # Need to create a 3d vector [samples, timesteps, input_dim]
            if self.conf['--model_type'].strip().lower() == 'lstm':
                X_train = X_train[:, newaxis, :]  # [samples, timesteps, input_dim]
                print 'modified training data to fit LSTM: ', X_train.shape
            from data_manipulator import roll_rows
            self.model.fit(X_train, roll_rows(X_train, rotate_forward_count)
                           , batch_size=int(self.conf['--batch_size'])
                           , nb_epoch=int(self.conf['--max_epochs'])
                           , validation_split=float(self.conf['--validation_ratio'])
                           , show_accuracy=True, shuffle=False, early_stop_lookback=3)
            print 'saving model to %s...' % os.path.join(self.model_dir, self.model_name)
            self.model.save_weights(os.path.join(self.model_dir, self.model_name))
        Grapher().plot(self.model, os.path.join(self.model_dir, 'model.png'))

    def add_autoencoder(self, encoder_sizes=[], decoder_sizes=[]):
        assert(len(encoder_sizes) != 0 and len(decoder_sizes) != 0)
        assert(len(encoder_sizes) == len(decoder_sizes))

        self.encoder_sizes = encoder_sizes
        self.decoder_sizes = decoder_sizes

        encoders = Sequential()
        decoders = Sequential()
        for i in range(0, len(encoder_sizes) - 1):
            encoders.add(Dense(encoder_sizes[i], encoder_sizes[i + 1]
                               , init=self.conf['--initialization']
                               , activation=self.conf['--activation']
                               , W_regularizer=zero))

            decoders.add(Dense(decoder_sizes[i], decoder_sizes[i + 1]
                               , init=self.conf['--initialization']
                               , activation=self.conf['--activation']
                               , W_regularizer=l2()))

        self.model.add(AutoEncoder(encoder=encoders
                                   , decoder=decoders
                                   , tie_weights=True
                                   , output_reconstruction=True))
        return self.model

    # TODO: This doesnt work yet
    # (batch size, stack size, nb row, nb col)
    def add_conv_autoencoder(self, encoder_sizes=[], decoder_sizes=[]):
        assert(len(encoder_sizes) != 0 and len(decoder_sizes) != 0)
        assert(len(encoder_sizes) == len(decoder_sizes))

        self.encoder_sizes = encoder_sizes
        self.decoder_sizes = decoder_sizes

        encoders = Sequential()
        decoders = Sequential()
        # for i in range(0, len(encoder_sizes) - 1):
        encoders.add(Convolution1D(32, 3, 3
                                      , activation=self.conf['--activation']
                                      , init=self.conf['--initialization']
                                      , border_mode='valid'))
        encoders.add(Activation('relu'))
        encoders.add(MaxPooling1D())
        encoders.add(Convolution1D(32, 1, 1
                                      , activation=self.conf['--activation']
                                      , init=self.conf['--initialization']
                                      , border_mode='valid'))

        decoders.add(Convolution1D(32, 1, 1
                                      , activation=self.conf['--activation']
                                      , init=self.conf['--initialization']
                                      , border_mode='valid'))
        decoders.add(Activation('relu'))
        decoders.add(MaxPooling1D())
        decoders.add(Convolution1D(32, 3, 3
                                      , activation=self.conf['--activation']
                                      , init=self.conf['--initialization']
                                      , border_mode='valid'))

        self.model.add(AutoEncoder(encoder=encoders
                                   , decoder=decoders
                                   , tie_weights=True
                                   , output_reconstruction=True))

    def add_lstm_autoencoder(self, encoder_sizes=[], decoder_sizes=[]):
        assert(len(encoder_sizes) != 0 and len(decoder_sizes) != 0)
        assert(len(encoder_sizes) == len(decoder_sizes))

        self.encoder_sizes = encoder_sizes
        self.decoder_sizes = decoder_sizes

        encoders = Sequential()
        decoders = Sequential()
        for i in range(0, len(encoder_sizes) - 1):
            encoders.add(LSTM(encoder_sizes[i], encoder_sizes[i + 1]
                              , activation=self.conf['--activation']
                              , inner_activation=self.conf['--inner_activation']
                              , init=self.conf['--initialization']
                              , inner_init=self.conf['--inner_init']
                              , truncate_gradient=int(self.conf['--truncated_gradient'])
                              , return_sequences=True))
            decoders.add(LSTM(decoder_sizes[i], decoder_sizes[i + 1]
                              , activation=self.conf['--activation']
                              , inner_activation=self.conf['--inner_activation']
                              , init=self.conf['--initialization']
                              , inner_init=self.conf['--inner_init']
                              , truncate_gradient=int(int(self.conf['--truncated_gradient']))
                              , return_sequences=not (i == len(encoder_sizes) - 1)))

        self.model.add(AutoEncoder(encoder=encoders
                                   , decoder=decoders
                                   , tie_weights=False
                                   , output_reconstruction=True))
        return self.model

    def predict_mse_mean(self, test):
        predictions = self.predict_mse(test)
        mse_predictions = predictions.mean(axis=1)
        assert len(mse_predictions) == len(test)
        return mse_predictions

    def predict_mse(self, test):
        from data_manipulator import elementwise_square, normalize
        predictions = self.predict(test)
        mse_predictions = elementwise_square(test - predictions)
        return mse_predictions

    def predict(self, test):
        # Need to create a 3d vector [samples, timesteps, input_dim]
        if self.conf['--model_type'].strip().lower() == 'lstm':
            test = test[:, newaxis, :]
        predictions = self.model.predict(test, 1, verbose=0)
        if len(predictions.shape) > 2:  # Resize the LSTM outputs
            predictions = predictions.reshape(predictions.shape[0], predictions.shape[2])
        return predictions

    def get_model(self):
        return self.model

    def get_model_type(self):
        return self.conf['--model_type']

    @staticmethod
    def load_model(path_str, model):
        if os.path.isfile(path_str):
            print 'model found, loading existing model...'
            model.load_weights(path_str)
            return True
        else:
            print 'model does not exist...'
            return False
