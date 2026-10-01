import numpy as np

from src.models.ensemble import build_ensemble
from src.models.autoencoder import build_autoencoder
from src.models.cnn import build_cnn


def main():
    # Generate sample data
    X = np.random.rand(20, 100).astype("float32")
    y = np.array([0, 1] * 10)

    print("Testing Ensemble...")
    ensemble = build_ensemble()
    ensemble.fit(X, y)
    predictions = ensemble.predict(X)
    print("Ensemble output shape:", predictions.shape)

    print("\nTesting Autoencoder...")
    autoencoder = build_autoencoder(100)
    reconstructed = autoencoder.predict(X, verbose=0)
    print("Autoencoder output shape:", reconstructed.shape)

    print("\nTesting CNN...")
    cnn = build_cnn(100)
    cnn_input = X.reshape(20, 100, 1)
    probabilities = cnn.predict(cnn_input, verbose=0)
    print("CNN output shape:", probabilities.shape)

    print("\nAll three model smoke tests passed!")


if __name__ == "__main__":
    main()