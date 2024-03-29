# -*- coding: utf-8 -*-
"""VAE Shape Analysis

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1A11t8-uEQEMTlbcjJe5KfriH8WEYu6Cu
"""

from google.colab import drive
drive.mount('/content/drive')

"""##### 1. Increase Model Complexity (Use a more complex encoder and decode)
##### 2. Use a larger latent space.
##### 3. L1 or L2 regularization.
##### 4. Try different loss functions
##### 5. Try different learning rate
##### 6. Try different activation function
##### 7. Increase the number of epochs
##### 8. Try adjusting the I/P dimensions

### LOADING & PREPROCESSING THE IMAGES
"""

import os
import cv2
import numpy as np
from PIL import Image
from sklearn.model_selection import train_test_split

directory = "/content/drive/My Drive/PD Dataset/Dataset"
height = 200
width = 200

# Get the list of image file names in the directory
image_files = os.listdir(directory)

# List to store the loaded images
images = []

# Loop through each image file
for file_name in image_files:

    # Construct the full path of the image file
    file_path = os.path.join(directory, file_name)

    # Load the image using PIL
    image = Image.open(file_path)

    # Process the image as per your requirements. For example, resize the image:
    image = image.resize((width, height))

    # Convert the image to float datatype
    image_float = np.array(image).astype(float)

    # Normalize the image
    image_float /= 255.0

    # Append the processed image to the list
    images.append(image_float)

images = np.array(images)

# images = images.reshape((114,600,600,3))
print(images.shape)

"""### SPLITTING THE DATASET"""

from sklearn.model_selection import train_test_split

# Shuffle the images.
np.random.shuffle(images)

# Split the images into a training set and a test set.
(x_train, x_test) = train_test_split(images, test_size=0.25)

# x_train = x_train[..., :3]
# x_test = x_test[..., :3]

print(x_train.shape)
print(x_test.shape)

print(x_train)

pip install optuna

"""### USING VARIATIONAL AUTO ENCODERS"""

import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from keras.layers import Input, Dense, Lambda, BatchNormalization, Dropout
from keras.optimizers import Adam,RMSprop
from keras.models import Model
from keras import backend as K
from keras.datasets import mnist
import optuna

class create_vae_model:

    def __init__(self, input_dim, num_hidden_layers, hidden_units, latent_dim, dropout_rate):
        self.input_dim = input_dim
        self.num_hidden_layers = num_hidden_layers
        self.hidden_units = hidden_units
        self.latent_dim = latent_dim
        self.dropout_rate = dropout_rate

    def encoder(self):

        inputs = Input(shape=self.input_dim)
        x = inputs

        for _ in range(self.num_hidden_layers):
            x = Dense(self.hidden_units, activation='relu')(x)
            x = Dropout(self.dropout_rate)(x)  # Add dropout regularization
        z_mean = Dense(self.latent_dim)(x)
        z_log_var = Dense(self.latent_dim)(x)
        return Model(inputs, [z_mean, z_log_var], name='encoder')

    def decoder(self):

        latent_inputs = Input(shape=self.latent_dim)
        x = latent_inputs

        for _ in range(self.num_hidden_layers):
            x = Dense(self.hidden_units, activation='relu')(x)
            x = Dropout(self.dropout_rate)(x)  # Add dropout regularization

        outputs = Dense(self.input_dim, activation='sigmoid')(x)
        return Model(latent_inputs, outputs, name='decoder')

    def sampling(self, args):

        z_mean, z_log_var = args
        epsilon = tf.random.normal(shape=(tf.shape(z_mean)[0], self.latent_dim), mean=0.0, stddev=1.0)

        return z_mean + tf.exp(0.5 * z_log_var) * epsilon

    def loss_function(self, inputs, outputs, z_mean, z_log_var):

        reconstruction_loss = K.sum(K.binary_crossentropy(inputs, outputs),axis=-1)
        kl_loss = -0.5 * tf.reduce_mean(1 + z_log_var - K.square(z_mean) - K.exp(z_log_var),axis=-1)

        return K.mean(reconstruction_loss + kl_loss)

    def model(self):

        inputs = Input(shape=self.input_dim)
        encoder = self.encoder()
        decoder = self.decoder()

        z_mean, z_log_var = encoder(inputs)
        z = Lambda(self.sampling)([z_mean, z_log_var])
        outputs = decoder(z)
        vae = Model(inputs, outputs, name='vae')
        vae_loss = self.loss_function(inputs, outputs, z_mean, z_log_var)
        vae.add_loss(vae_loss)

        return vae

    def objective(self, trial):

        # Define the hyperparameters to tune
        batch_size = trial.suggest_categorical('batch_size', [16, 32, 64,128])
        optimizer = trial.suggest_categorical('optimizer', ['adam', 'rmsprop'])
        num_epochs = trial.suggest_int('num_epochs', 50, 200, step=50)

        # Build the VAE model
        vae = self.model()

        # Compile the model with the specified optimizer
        if optimizer == 'adam':
            optimizer = Adam()

        else:
            optimizer = RMSprop()

        vae.compile(optimizer=optimizer)

        # Train the model
        vae.fit(x_train, batch_size=batch_size, epochs=num_epochs, validation_data=(x_test, None))

        # Calculate the validation loss
        validation_loss = vae.evaluate(x_test, batch_size=batch_size)

        return validation_loss

    def train(self, x_train, x_val):

        # Define the study for hyperparameter optimization
        study = optuna.create_study(direction='minimize')

        # Run the hyperparameter optimization
        study.optimize(self.objective, n_trials=10)

        # Get the best hyperparameters
        best_params = study.best_params

        # Build the VAE model with the best hyperparameters
        vae = self.model()
        vae.compile(optimizer=best_params['optimizer'])
        vae.fit(x_train, batch_size=best_params['batch_size'], epochs=best_params['num_epochs'], validation_data=(x_val, None))
        decoder_ = self.decoder()

        return vae, best_params, decoder_

x_train = x_train.reshape(-1,40000)
x_test = x_test.reshape(-1,40000)

print(x_train.shape)
print(x_test.shape)

input_dim = 40000
num_hidden_layers = 5
hidden_units = 256
latent_dim = 10
dropout_rate = 0.2

vae_model = create_vae_model(input_dim, num_hidden_layers, hidden_units, latent_dim, dropout_rate)
best_vae_model, best_hyperparameters, prediction_decoder= vae_model.train(x_train, x_test)

"""### PLOTTING THE SAMPLES"""

import numpy as np
import matplotlib.pyplot as plt

# Assuming you have trained the VAE model and have the trained decoder model available

# Generate random samples
num_samples = 10  # Number of random samples to generate
latent_dim = 10  # Latent dimension of the VAE model

# Generate random latent vectors
random_latent_vectors = np.random.normal(size=(num_samples, latent_dim))

# Generate samples using the decoder model
decoded_samples = prediction_decoder.predict(random_latent_vectors)

# Assuming your input data is images, you can reshape and visualize the generated images
fig, axes = plt.subplots(1, num_samples, figsize=(12, 4))

for i in range(num_samples):
    generated_image = decoded_samples[i].reshape(200,200)  # Reshape to the appropriate image shape
    axes[i].imshow(generated_image, cmap='gray')  # Assuming grayscale images, adjust the colormap if needed
    axes[i].axis('off')

plt.show()

"""### PRINTING THE LATENT REPRESENTATION OF MASKS/IMAGES"""

print(random_latent_vectors)

print(decoded_samples.shape)
print(decoded_samples[0].shape)

print(decoded_samples)

reduced_dimension = decoded_samples.reshape((400000))

print(reduced_dimension)
print(reduced_dimension.shape)

"""### ATTACHING A MACHINE LEARNING CLASSIFIER"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Load the latent representations of the images.
latent_representations = np.load("latent_representations.npy")

# Load the labels of the images.
labels = pd.read_csv("labels.csv")["label"].values

# Choose a classifier.
classifier = RandomForestClassifier()

# Train the classifier.
classifier.fit(latent_representations, labels)

# Test the classifier.
test_latent_representations = np.load("test_latent_representations.npy")
test_labels = pd.read_csv("test_labels.csv")["label"].values

predictions = classifier.predict(test_latent_representations)

# Calculate the accuracy of the classifier.
accuracy = np.mean(predictions == test_labels)

print("Accuracy:", accuracy)

# Use the classifier to make predictions.
new_latent_representation = np.load("new_latent_representation.npy")
prediction = classifier.predict(new_latent_representation)

print("Prediction:", prediction)

"""## USING FASHION-MNIST

### Importing Modules
"""

# Commented out IPython magic to ensure Python compatibility.
# import the necessary packages
import imageio
import glob
import os
import time
import cv2
import tensorflow as tf
from tensorflow.keras import layers
from IPython import display
import matplotlib.pyplot as plt
import numpy as np
# %matplotlib inline
from tensorflow import keras

"""### Loading and Preprocessing Dataset"""

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.fashion_mnist.load_data()
x_train = x_train.reshape(x_train.shape[0], 28, 28, 1).astype('float32')
x_test = x_test.astype('float32')
x_train = x_train / 255.
x_test = x_test / 255.

# Batch and shuffle the data
train_dataset = tf.data.Dataset.from_tensor_slices(x_train).\
shuffle(60000).batch(128)

"""### Define the Encoder Network"""

def encoder(input_encoder):

    inputs = keras.Input(shape=input_encoder, name='input_layer')
    # Block 1
    x = layers.Conv2D(32, kernel_size=3, strides= 1, padding='same', name='conv_1')(inputs)
    x = layers.BatchNormalization(name='bn_1')(x)
    x = layers.LeakyReLU(name='lrelu_1')(x)

    # Block 2
    x = layers.Conv2D(64, kernel_size=3, strides= 2, padding='same', name='conv_2')(x)
    x = layers.BatchNormalization(name='bn_2')(x)
    x = layers.LeakyReLU(name='lrelu_2')(x)

    # Block 3
    x = layers.Conv2D(64, 3, 2, padding='same', name='conv_3')(x)
    x = layers.BatchNormalization(name='bn_3')(x)
    x = layers.LeakyReLU(name='lrelu_3')(x)

    # Block 4
    x = layers.Conv2D(64, 3, 1, padding='same', name='conv_4')(x)
    x = layers.BatchNormalization(name='bn_4')(x)
    x = layers.LeakyReLU(name='lrelu_4')(x)

    # Final Block
    flatten = layers.Flatten()(x)
    bottleneck = layers.Dense(2, name='dense_1')(flatten)
    model = tf.keras.Model(inputs, bottleneck, name="Encoder")
    return model

"""### The Sampling Network"""

# def sampling(input_1,input_2):
#     mean = keras.Input(shape=input_1, name='input_layer1')
#     log_var = keras.Input(shape=input_2, name='input_layer2')
#     out = layers.Lambda(sampling_reparameterization_model, name='encoder_output')([mean, log_var])
#     enc_2 = tf.keras.Model([mean,log_var], out,  name="Encoder_2")
#     return enc_2

# def sampling_reparameterization(distribution_params):
#     mean, log_var = distribution_params
#     epsilon = K.random_normal(shape=K.shape(mean), mean=0., stddev=1.)
#     z = mean + K.exp(log_var / 2) * epsilon
#     return z

"""### Define the Decoder Network"""

def decoder(input_decoder):
    # Initial Block
    inputs = keras.Input(shape=input_decoder, name='input_layer')
    x = layers.Dense(3136, name='dense_1')(inputs)
    x = tf.reshape(x, [-1, 7, 7, 64], name='Reshape_Layer')

    # Block 1
    x = layers.Conv2DTranspose(64, 3, strides= 1, padding='same',name='conv_transpose_1')(x)
    x = layers.BatchNormalization(name='bn_1')(x)
    x = layers.LeakyReLU(name='lrelu_1')(x)

    # Block 2
    x = layers.Conv2DTranspose(64, 3, strides= 2, padding='same', name='conv_transpose_2')(x)
    x = layers.BatchNormalization(name='bn_2')(x)
    x = layers.LeakyReLU(name='lrelu_2')(x)

    # Block 3
    x = layers.Conv2DTranspose(32, 3, 2, padding='same', name='conv_transpose_3')(x)
    x = layers.BatchNormalization(name='bn_3')(x)
    x = layers.LeakyReLU(name='lrelu_3')(x)

    # Block 4
    outputs = layers.Conv2DTranspose(1, 3, 1,padding='same', activation='sigmoid', name='conv_transpose_4')(x)
    model = tf.keras.Model(inputs, outputs, name="Decoder")
    return model

"""### Optimizer and Loss Function"""

optimizer = tf.keras.optimizers.Adam(learning_rate= 0.0005)
def ae_loss(y_true, y_pred):
    loss = K.mean(K.square(y_true - y_pred), axis = [1,2,3])
    return loss

"""### Training the Variational Autoencoder"""

# Notice the use of `tf.function`
# This annotation causes the function to be "compiled".
@tf.function
def train_step(images):

    with tf.GradientTape() as encoder, tf.GradientTape() as decoder:

        latent = encoder(images, training=True)
        generated_images = decoder(latent, training=True)
        loss = ae_loss(images, generated_images)

    gradients_of_enc = encoder.gradient(loss, encoder.trainable_variables)
    gradients_of_dec = decoder.gradient(loss, decoder.trainable_variables)


    optimizer.apply_gradients(zip(gradients_of_enc, encoder.trainable_variables))
    optimizer.apply_gradients(zip(gradients_of_dec, decoder.trainable_variables))
    return loss

def train(dataset, epochs):
  for epoch in range(epochs):
    start = time.time()
    for image_batch in dataset:
      train_step(image_batch)

    print ('Time for epoch {} is {} sec'.format(epoch + 1, time.time()-start))

train(train_dataset, epoch)

figsize = 15

latent = encoder.predict(x_test[:25])
reconst = decoder.predict(latent)

fig = plt.figure(figsize=(figsize, 10))

for i in range(25):
    ax = fig.add_subplot(5, 5, i+1)
    ax.axis('off')
    ax.text(0.5, -0.15, str(label_dict[y_test[i]]), fontsize=10, ha='center', transform=ax.transAxes)

ax.imshow(reconst[i, :,:,0]*255, cmap = 'gray')













