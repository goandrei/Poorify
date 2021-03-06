import torch.nn as nn
import torch
from torch.optim import Adam, SGD
import logging
from tqdm import tqdm
import time

#in-house imports
from models.model import MyModel
from visualizer import plot_loss
from emotionClasification import Emotion, findEmotion
import constants

class Trainer():
    def __init__(self, model, vocab, train_generator,
                 val_generator, epochs=10, batch_size=32,
                 max_grad_norm=5.0, lr=0.001, loss = 'mse',
                 optim='adam', train_verbose=10, val_verbose=5):

        self.model = model
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.max_grad_norm = max_grad_norm
        self.vocab = vocab

        self.train_generator = train_generator
        self.val_generator = val_generator

        self.train_generator_size = len(train_generator)
        self.val_generator_size = len(val_generator)

        self.train_verbose = train_verbose
        self.val_verbose = val_verbose

        if optim == 'adam':
            self.optimizer = Adam(self.model.parameters(), lr = self.lr)
        elif optim == 'SGD':
            self.optimizer = SGD(self.model.parameters(), lr = self.lr)

        if loss == 'mse':
            self.loss_fn = nn.MSELoss()
        if loss == 'CrossEntropy':
            self.loss_fn = nn.CrossEntropyLoss()
        logging.info('Trainer created!')

    def train_epoch(self, epoch):

        epoch_loss = 0.0
        #use a 0s tensor as starting hidden state
        t = time.time()
        prev_hidden = (torch.zeros(1, 1, self.model.rnn_size).to(constants.DEVICE), torch.zeros(1, 1, self.model.rnn_size).to(constants.DEVICE))
        for idx, (sample, label) in enumerate(self.train_generator):


            if sample.shape[0] < self.batch_size:
                continue

            sample = sample.to(constants.DEVICE)
            label = label.to(constants.DEVICE)
            sample = sample.transpose(1,0)

            seq_len = int(sample.size(1) / self.model.embedding_size)
            print(self.model.vocab_size)

            #reset the gradients
            self.optimizer.zero_grad()
            print(sample.size())

            (hidden_state, rnn_out) = self.model(sample.unsqueeze(2), prev_hidden)

            print('rnn_out gata')

            batch_loss = self.loss_fn(rnn_out.squeeze(), torch.max(label.int(), 1)[1])
            print('batch_loss gata')

            epoch_loss += batch_loss.item()

            batch_loss.backward()
            print('backward gata')

            #clip the gradients to avoid explosions
            torch.nn.utils.clip_grad_norm_(list(self.model.parameters()), self.max_grad_norm)
            print('max_grad gata')

            #update the parameters
            self.optimizer.step()
            print('optimizer gata')

            #use generated hidden state as the next input hidden states
            hidden_state0 = hidden_state[0].detach_()
            hidden_state1 = hidden_state[1].detach_()
            prev_hidden = (hidden_state0, hidden_state1)

            if idx % self.train_verbose == 0:
                print('Epoch {} - batch {} / {} -  train loss : {}'.format(epoch, idx, self.train_generator_size, batch_loss.item()))

        return epoch_loss / self.train_generator_size

    def val_epoch(self, epoch, hidden_start=None):

        #validation epoch won't do any updates
        with torch.no_grad():
            epoch_loss = 0.0
            prev_hidden = torch.zeros(self.batch_size, self.model.rnn_size).to(constants.DEVICE)

            for idx, (sample, label) in enumerate(self.val_generator):

                if sample.shape[0] < self.batch_size:
                    continue

                sample = sample.to(constants.DEVICE)
                label = label.to(constants.DEVICE)

                hidden_state = self.model(sample, prev_hidden)
                logits = self.model.get_logits(hidden_state)
                batch_loss = self.loss_fn(logits, label.long())
                epoch_loss += batch_loss.item()

                prev_hidden = hidden_state
                print(logits.size())
                predicted_emotions = [int(torch.max(l,0)[1].item()) for l in logits]
                label_emotions = label.int()

                #will result a vector of 0s and 1s(True/False)
                #summing them will get us the number of correct answers
                acc = torch.sum(torch.tensor([predict == label for predict, label in zip(predicted_emotions, label_emotions)]))

                if idx % self.val_verbose == 0:
                    print('Epoch {} - batch {} / {} - validation loss : {} - accuracy : {}'.format(epoch, idx, self.val_generator_size, \
                                                                                                   batch_loss.item(), acc.item() / self.batch_size))

            return epoch_loss / self.val_generator_size

    def train(self):

        logging.info('Starting the training...')

        train_loss = []
        val_loss = []
        hidden_start = torch.zeros(self.batch_size, self.model.rnn_size)
        for e in tqdm(range(self.epochs), ascii=True, desc='Epochs'):
            t_loss = self.train_epoch(e)
            v_loss = self.val_epoch(e, hidden_start)

            #keep the losses from each epoch
            train_loss.append(t_loss)
            val_loss.append(v_loss)

        plot_loss(train_loss, val_loss)
