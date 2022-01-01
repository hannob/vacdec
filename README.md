# vacdec
Python script to decode the EU Covid-19 vaccine certificate, as [specified by the EU](https://ec.europa.eu/health/ehealth/covid-19_en).

This script takes an image with a QR code of a vaccine certificate as
the parameter and will show the certificate's content.
**It will not validate the signature.**

A [fork of this script with signature verification exists](https://github.com/HQJaTu/vacdec/tree/signature-verification).

The code is very short and should provide an easy way to understand
how these certificates are encoded:

* The QR code encodes a string starting with "HC1:".
* The string following "HC1:" is base45 encoded.
* Decoding the base45 leads to zlib-compressed data.
* Decompression leads to a CBOR Web Token structure.

## setup

You will need the python pillow, pyzbar, cbor2 and base45 packages. Additionally, you need zbar. For Mac OS X, it can be installed via `brew install zbar`, on Debian systems via `apt install libzbar0`. [Source](https://pypi.org/project/pyzbar/)

You can install them via your distribution or via pip:

```
pip install base45 cbor2 pillow pyzbar
```

## usage

Run:

```
./vacdec [image]
```

[image] can be an image in any format pillow supports, including of
course PNG and JPG.

The certificate can also be provided as string via command line with the option `-c` or from a text file with the option `-t`.

There's also a verbose mode (`-v`) that translates the dates from Unix to UTC and decodes the json field values (name of the vaccine, type of test...).

A test certificate can be found [here](https://github.com/Digitaler-Impfnachweis/certification-apis/tree/master/examples).

## author

Written by [Hanno Böck](https://hboeck.de/).
