"""Prototype autoencoder for IoT anomaly detection."""

from keras import Model
from keras.layers import Input, Dense


def build_autoencoder(input_dim):
    inputs = Input(shape=(input_dim,))

    encoded = Dense(64, activation="relu")(inputs)
    encoded = Dense(32, activation="relu")(encoded)

    decoded = Dense(64, activation="relu")(encoded)
    outputs = Dense(input_dim, activation="linear")(decoded)

    model = Model(inputs, outputs)
    model.compile(optimizer="adam", loss="mse")

    return model