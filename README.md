# vacdec
Python script to decode the EU Covid-19 vaccine certificate

This script takes an image with a QR code of a vaccine certificate as
the parameter and will show the certificate's content. It will not
validate the signature.

The code is very short and should provide an easy way to understand
how these certificates are encoded:

* The QR code encodes a string starting with "HC1:".
* The string following "HC1:" is base45 encoded.
* Decoding the base45 leads to zlib-compressed data.
* Decompression leads to a CBOR Web Token structure.

## setup

You need to install the following external dependencies:

```
pip install base45 cbor2 pillow pyzbar
```

## usage

You can either run it via:

```
python vacdec
```

or make the script executable and run it directly:

```
chmod u+x vacdec
./vacdec
```

Written by [Hanno Böck](https://hboeck.de/).
