import pandas as pd
import numpy as np
from pathlib import Path

PATH = Path("../data/test.csv")

"""
naive Bayes
P(result | A, B, C) = P(A | res)*P(B | res)*P(C | res) * P(res)
only solve binary sort
"""

class NaiveBayes:
  def __init__(self, prior: float) -> None:
    self.prior = prior
    self.data = pd.read_csv(PATH)
    self.all_type: dict[str, np.ndarray] = dict()
    for i in self.data.columns:
      self.all_type[i] = self.data[i].unique()
  
  def calculate(self, samples: list) -> float:
    return self.helper(1, samples) > self.helper(0, samples)
  
  def helper(self, state: int, samples: list) -> float:
    result: float = abs(1 - state - self.prior)
    temp = self.data[self.data["result"] == state]
    for i, sample in enumerate(samples):
      i: str = self.data.columns[i]
      result *= (1 + temp[temp[i] == sample].shape[0]) / (len(self.all_type[i]) + temp.shape[0])
    return result
  
def main() -> None:
  nai = NaiveBayes(0.5)
  print(nai.calculate([1, 1, 1]))



if __name__ == "__main__":
  main()