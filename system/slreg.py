import numpy as np


def sigmoid(a):
    """Sigmoid function of an array."""
    return 1 / (1 + np.exp(-a))


def predict_prob(X, theta):
    """Compute predicted probabilities."""
    return sigmoid(X @ theta)


def gradient_descent(X, y, theta, alpha):
    """Gradient descent for logistic regression.
    
    Although stochastic gradient descent uses only one example at a time, for generalizability
    we use a vectorized implementation.
    
    Returns
    -------
    theta : array
        Updated theta.
        
    J : float
        Cost function for logistic regression.
    """
    
    m = len(y)
    pred = predict_prob(X, theta)
    theta = theta - alpha / m * X.T @ (pred - y)
    J = 1 / m * (- y @ np.log(pred + 1e-13) - (1 - y) @ np.log(1 - pred + 1e-13))
    return theta, J