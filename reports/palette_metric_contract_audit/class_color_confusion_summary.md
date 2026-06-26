# Class-Color Confusion Summary

Status: **NOT VERIFIED locally**.

Reason: prediction and quantized output images are not present in this local snapshot.

Important distinction: unknown color rate only checks whether colors are inside the frozen palette. It does not detect class-color swaps. A generated desk quantized to the double-bed RGB has unknown color rate 0, but is still a semantic class-color error. The new audit computes target category vs quantized predicted category confusion when predictions are available.
