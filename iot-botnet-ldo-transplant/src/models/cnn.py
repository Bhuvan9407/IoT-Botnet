"""1D-CNN prototype for IoT botnet detection."""

from keras import Sequential
from keras.layers import Input, Conv1D, MaxPooling1D, Flatten, Dense


def build_cnn(input_dim):
    model = Sequential([
        Input(shape=(input_dim, 1)),
        Conv1D(16, kernel_size=3, activation="relu"),
        MaxPooling1D(pool_size=2),
        Flatten(),
        Dense(32, activation="relu"),
        Dense(1, activation="sigmoid")
    ])

    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"]
    )

    return model