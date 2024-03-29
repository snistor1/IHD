import random

from keras.utils import Sequence
from utilities.augmentations import *
from Preprocessor import Preprocessor


class DataGenerator(Sequence):

    def __init__(self, list_ids, labels=None, batch_size=1, img_size=(512, 512, 3),
                 img_dir=TRAIN_DIR_STAGE_2, shuffle=True, n_classes=2):
        self.list_ids = list_ids
        self.indices = np.arange(len(self.list_ids))
        self.labels = labels
        self.batch_size = batch_size
        self.img_size = img_size
        self.img_dir = img_dir
        self.shuffle = shuffle
        self.n_classes = n_classes
        # TODO: this could be generalized with the help of
        # an Augmenter class
        self.n_augment = 3  # 3 data augmentation functions
        self.augment_funcs = [blur_image,
                              noisy,
                              adjust_brightness,
                              lambda img: img]  # identity function
        self.on_epoch_end()
        if labels is not None:
            # Weights should be a probability distribution.
            # If the number of training instances is too large,
            # there could be issues! (arithmetic underflow)
            weight_func = lambda row: 1.0 if row["any"] == 0 else self.n_augment + 1
            self.weights = labels.apply(weight_func, axis=1)
            total = self.weights.sum()
            self.weights = (self.weights / total).values
        # set random seed, hope this randomizes starting value for
        # each worker
        random.seed(os.urandom(8))

    def __len__(self):
        return len(self.indices) // self.batch_size

    def __getitem__(self, index):
        indices = np.random.choice(self.indices, size=self.batch_size,
                                   replace=False, p=self.weights)
        return self.__data_generation(indices)

    # Don't think this is necessary anymore, indices are sampled randomly.
    def on_epoch_end(self):
        pass

    def __data_generation(self, indices):
        x = np.empty((self.batch_size, *self.img_size))
        if self.labels is not None:  # training phase
            if self.n_classes == 2:
                y = np.empty((self.batch_size,), dtype=np.float32)
            else:
                y = np.empty((self.batch_size, self.n_classes), dtype=np.float32)
            for i, idx in enumerate(indices):
                image = Preprocessor.preprocess(self.img_dir + self.list_ids[idx] + ".dcm")
                if self.labels.iloc[idx]['any'] == 1:
                    image = self.augment_funcs[random.randint(0, self.n_augment)](image)
                image = np.array(image)
                image = np.repeat(image[..., np.newaxis], 3, -1)
                x[i, ] = image
                if self.n_classes == 2:
                    y[i, ] = self.labels.iloc[idx]['any']
                elif self.n_classes == 5:
                    y[i, ] = self.labels.iloc[idx, 1:]
                else:
                    y[i, ] = self.labels.iloc[idx]
            return x, y
        else:  # test phase
            for i, idx in enumerate(indices):
                image = Preprocessor.preprocess(self.img_dir + self.list_ids[idx] + ".dcm")
                image = np.repeat(image[..., np.newaxis], 3, -1)
                x[i, ] = image
            return x
