"""
export_tflite.py
================
Convert the fine-tuned DistilBERT model (model/artifacts/) to TensorFlow Lite
with dynamic-range int8 quantization, for on-device inference on Android.

Pipeline:
  HF PyTorch model -> TF model (from_pt=True) -> concrete function with fixed
  input shapes -> TFLiteConverter (int8 dynamic range) -> model.tflite

Also confirms vocab.txt is present (the WordPiece vocabulary embedded on Android).

Run (after train.py):
    python model/export_tflite.py --seq-len 128

Acceptance criterion (Phase 5): model.tflite < 100 MB, inference < 500 ms.
"""

from __future__ import annotations

import argparse
import os

ARTIFACTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seq-len", type=int, default=128)
    args = p.parse_args()

    import tensorflow as tf
    from transformers import TFDistilBertForSequenceClassification

    if not os.path.exists(os.path.join(ARTIFACTS, "config.json")):
        raise SystemExit("No model in model/artifacts/. Run train.py first.")

    # Load the PyTorch weights into the TF model implementation.
    model = TFDistilBertForSequenceClassification.from_pretrained(
        ARTIFACTS, from_pt=True)

    seq = args.seq_len

    # Build a concrete function with fixed input shapes (required by TFLite).
    @tf.function(input_signature=[
        tf.TensorSpec([1, seq], tf.int32, name="input_ids"),
        tf.TensorSpec([1, seq], tf.int32, name="attention_mask"),
    ])
    def serving(input_ids, attention_mask):
        out = model({"input_ids": input_ids, "attention_mask": attention_mask})
        return {"logits": out.logits}

    concrete = serving.get_concrete_function()

    converter = tf.lite.TFLiteConverter.from_concrete_functions([concrete], model)
    # Dynamic-range int8 quantization: ~4x smaller, no calibration dataset needed.
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,  # some BERT ops need this
    ]
    tflite_model = converter.convert()

    out_path = os.path.join(ARTIFACTS, "model.tflite")
    with open(out_path, "wb") as f:
        f.write(tflite_model)

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"[export] wrote {out_path} ({size_mb:.1f} MB)")
    print(f"[check] size < 100 MB: {'PASS' if size_mb < 100 else 'FAIL'}")

    vocab = os.path.join(ARTIFACTS, "vocab.txt")
    if os.path.exists(vocab):
        print(f"[check] tokenizer vocab present: {vocab}")
        print("        -> copy model.tflite and vocab.txt to "
              "android-app/app/src/main/assets/")
    else:
        print("[warn] vocab.txt missing; re-run train.py to save the tokenizer.")


if __name__ == "__main__":
    main()
