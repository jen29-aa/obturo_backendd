import numpy as np

def topsis(matrix, weights, impacts):
    """
    matrix: 2D list of criteria values
    weights: list of weights
    impacts: list containing '+' for benefit, '-' for cost
    """
    matrix = np.array(matrix, dtype=float)
    rows, cols = matrix.shape

    # Step 1: Normalization
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # Step 2: Weighting
    weighted = normalized * weights

    # Step 3: Identify ideal best and worst
    ideal_best = []
    ideal_worst = []

    for j in range(cols):
        if impacts[j] == '+':
            ideal_best.append(weighted[:, j].max())
            ideal_worst.append(weighted[:, j].min())
        else:
            ideal_best.append(weighted[:, j].min())
            ideal_worst.append(weighted[:, j].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # Step 4: Distances
    d_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # Step 5: TOPSIS score
    denominator = d_best + d_worst
    # Handle division by zero - if both distances are 0, assign middle score
    scores = np.divide(d_worst, denominator, where=denominator!=0, out=np.full_like(d_worst, 0.5))
    
    # Convert NaN to 0.5
    scores = np.nan_to_num(scores, nan=0.5)

    return scores.tolist()
