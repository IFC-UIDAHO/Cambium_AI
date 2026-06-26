# Fictional toy: "model" vs baseline on synthetic data. Intentionally contains a leakage smell
# (the feature is built from the target) for the Verification boards to catch.
import numpy as np
rng=np.random.default_rng(0); n=400
y=rng.normal(size=n)
x_leaky=y+rng.normal(scale=0.1,size=n)      # <-- leakage: feature ~ target
pred=x_leaky                                  # "model"
rmse=float(np.sqrt(np.mean((pred-y)**2)))
print(f"RMSE={rmse:.3f}  (suspiciously low -> check for leakage)")
