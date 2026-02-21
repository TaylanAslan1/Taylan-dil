import json
import os
from typing import List

__all__ = [
    "ml_model_olustur",
    "ml_egit",
    "ml_tahmin",
]


def _model_path(path: str) -> str:
    return path


def ml_model_olustur(path: str, input_size: int) -> str:
    weights = [0.0 for _ in range(int(input_size))]
    model = {"input_size": int(input_size), "weights": weights, "bias": 0.0}
    with open(_model_path(path), "w", encoding="utf-8") as f:
        json.dump(model, f)
    return path


def _load_model(path: str):
    with open(_model_path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def _save_model(path: str, model) -> None:
    with open(_model_path(path), "w", encoding="utf-8") as f:
        json.dump(model, f)


def _parse_vec(csv_str: str) -> List[float]:
    return [float(x.strip()) for x in csv_str.split(",") if x.strip()]


def ml_egit(path: str, inputs_csv: str, labels_csv: str, epochs: int, lr: float) -> str:
    model = _load_model(path)
    X = _parse_vec(inputs_csv)
    y = _parse_vec(labels_csv)
    if len(X) % model["input_size"] != 0:
        raise ValueError("input_size ile uyusmuyor")
    samples = len(X) // model["input_size"]
    if len(y) != samples:
        raise ValueError("label sayisi uyusmuyor")

    weights = model["weights"]
    bias = model["bias"]

    for _ in range(int(epochs)):
        for i in range(samples):
            start = i * model["input_size"]
            vec = X[start:start + model["input_size"]]
            pred = sum(w * v for w, v in zip(weights, vec)) + bias
            err = y[i] - pred
            for j in range(len(weights)):
                weights[j] += lr * err * vec[j]
            bias += lr * err

    model["weights"] = weights
    model["bias"] = bias
    _save_model(path, model)
    return "ok"


def ml_tahmin(path: str, input_csv: str) -> float:
    model = _load_model(path)
    vec = _parse_vec(input_csv)
    if len(vec) != model["input_size"]:
        raise ValueError("input_size ile uyusmuyor")
    return sum(w * v for w, v in zip(model["weights"], vec)) + model["bias"]


__all__.extend(["ml_sigmoid", "ml_sinir"])


def ml_sigmoid(x: float) -> float:
    import math
    return 1.0 / (1.0 + math.exp(-x))


def ml_sinir(path: str, input_csv: str) -> float:
    # simple sigmoid output
    val = ml_tahmin(path, input_csv)
    return ml_sigmoid(val)


__all__.extend(["ml_nn_olustur", "ml_nn_egit", "ml_nn_tahmin"])


def _rand_w(n):
    import random
    return [random.uniform(-0.5, 0.5) for _ in range(n)]


def ml_nn_olustur(path: str, input_size: int, hidden_size: int, output_size: int) -> str:
    model = {
        "input_size": int(input_size),
        "hidden_size": int(hidden_size),
        "output_size": int(output_size),
        "w1": [_rand_w(int(input_size)) for _ in range(int(hidden_size))],
        "b1": _rand_w(int(hidden_size)),
        "w2": [_rand_w(int(hidden_size)) for _ in range(int(output_size))],
        "b2": _rand_w(int(output_size)),
    }
    with open(_model_path(path), "w", encoding="utf-8") as f:
        json.dump(model, f)
    return path


def _sig(x):
    import math
    return 1.0 / (1.0 + math.exp(-x))


def _sig_deriv(y):
    return y * (1.0 - y)


def ml_nn_egit(path: str, inputs_csv: str, labels_csv: str, epochs: int, lr: float) -> str:
    model = _load_model(path)
    X = _parse_vec(inputs_csv)
    y = _parse_vec(labels_csv)
    ins = model["input_size"]
    h = model["hidden_size"]
    out = model["output_size"]
    if len(X) % ins != 0:
        raise ValueError("input_size ile uyusmuyor")
    samples = len(X) // ins
    if len(y) != samples * out:
        raise ValueError("label sayisi uyusmuyor")

    w1 = model["w1"]
    b1 = model["b1"]
    w2 = model["w2"]
    b2 = model["b2"]

    for _ in range(int(epochs)):
        for i in range(samples):
            x = X[i*ins:(i+1)*ins]
            y_true = y[i*out:(i+1)*out]

            # forward hidden
            h_out = []
            for j in range(h):
                s = sum(w1[j][k] * x[k] for k in range(ins)) + b1[j]
                h_out.append(_sig(s))

            # forward output
            o_out = []
            for j in range(out):
                s = sum(w2[j][k] * h_out[k] for k in range(h)) + b2[j]
                o_out.append(_sig(s))

            # output error
            o_err = [y_true[j] - o_out[j] for j in range(out)]
            o_delta = [o_err[j] * _sig_deriv(o_out[j]) for j in range(out)]

            # hidden error
            h_err = []
            for j in range(h):
                s = sum(w2[k][j] * o_delta[k] for k in range(out))
                h_err.append(s)
            h_delta = [h_err[j] * _sig_deriv(h_out[j]) for j in range(h)]

            # update w2,b2
            for j in range(out):
                for k in range(h):
                    w2[j][k] += lr * o_delta[j] * h_out[k]
                b2[j] += lr * o_delta[j]

            # update w1,b1
            for j in range(h):
                for k in range(ins):
                    w1[j][k] += lr * h_delta[j] * x[k]
                b1[j] += lr * h_delta[j]

    model["w1"] = w1
    model["b1"] = b1
    model["w2"] = w2
    model["b2"] = b2
    _save_model(path, model)
    return "ok"


def ml_nn_tahmin(path: str, input_csv: str):
    model = _load_model(path)
    x = _parse_vec(input_csv)
    ins = model["input_size"]
    h = model["hidden_size"]
    out = model["output_size"]
    if len(x) != ins:
        raise ValueError("input_size ile uyusmuyor")

    h_out = []
    for j in range(h):
        s = sum(model["w1"][j][k] * x[k] for k in range(ins)) + model["b1"][j]
        h_out.append(_sig(s))

    o_out = []
    for j in range(out):
        s = sum(model["w2"][j][k] * h_out[k] for k in range(h)) + model["b2"][j]
        o_out.append(_sig(s))

    if out == 1:
        return o_out[0]
    return ",".join(str(v) for v in o_out)
