#!/usr/bin/env python3

# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import os
import sys
import argparse

from datetime import datetime
import requests
import json
import base64
import cbor2
from cose.messages import CoseMessage, Sign1Message
from cose.keys import cosekey, keyops, keyparam, curves, keytype
from cose import algorithms

from cryptography import x509
from cryptography.hazmat import primitives

import logging

log = logging.getLogger(__name__)

DEFAULT_CERTS_DIR = "certs"
API_COUNTRY_AUSTRIA = "Austria"
API_COUNTRIES = (API_COUNTRY_AUSTRIA)

API_ENDPOINT_AUSTRIA = "https://greencheck.gv.at/api/masterdata"


def _setup_logger() -> None:
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(log_formatter)
    console_handler.propagate = False
    logging.getLogger().addHandler(console_handler)
    # log.setLevel(logging.DEBUG)
    log.setLevel(logging.INFO)


def fetch_certificates(country_to_use: str, destination_dir: str) -> dict:
    if country_to_use == API_COUNTRY_AUSTRIA:
        return fetch_certificates_austria_api(destination_dir)

    raise ValueError("Don't know what to do with country {0}!".format(country_to_use))


def _cert_to_cose_key(cert: x509.Certificate) -> cosekey.CoseKey:
    public_key = cert.public_key()
    key_dict = None

    if isinstance(public_key, primitives.asymmetric.ec.EllipticCurvePublicKey):
        curve_name = public_key.curve.name
        matching_curve = None
        for name in dir(curves):
            if name.startswith('_'):
                continue
            if curve_name.lower() == name.lower():
                if name == 'SECP256R1':
                    matching_curve = curves.P256
                elif name == 'SECP384R1':
                    matching_curve = curves.P384
                else:
                    raise RuntimeError("Unknown curve {}!".format(curve_name))
                break

        if not matching_curve:
            raise RuntimeError("Could not find curve {} used in X.509 certificate from COSE!".format(curve_name))

        public_numbers = public_key.public_numbers()
        size_bytes = public_key.curve.key_size // 8
        x = public_numbers.x.to_bytes(size_bytes, byteorder="big")
        y = public_numbers.y.to_bytes(size_bytes, byteorder="big")
        key_dict = {
            keyparam.KpKeyOps: [keyops.VerifyOp],
            keyparam.KpKty: keytype.KtyEC2,
            keyparam.EC2KpCurve: matching_curve,
            keyparam.KpAlg: algorithms.Es256,
            keyparam.EC2KpX: x,
            keyparam.EC2KpY: y,
        }
    else:
        raise RuntimeError("Cannot handle RSA-keys!")

    key = cosekey.CoseKey.from_dict(key_dict)

    return key


def _save_certs(trusted_list: bytes, destination_dir: str) -> dict:
    certs_out = {}
    cert_list = cbor2.loads(trusted_list)
    for cert_item in cert_list["c"]:
        key_id = cert_item["i"]
        if "c" in cert_item:
            cert_der_data = cert_item["c"]
            cert = x509.load_der_x509_certificate(cert_der_data)
        else:
            raise NotImplemented("Cannot construct X.509 certificate from parts!")

        if key_id in certs_out:
            log.warning("Duplicate certificate with key ID{}!".format(key_id.hex()))

        certs_out[key_id] = cert

    # Save
    old_mask = os.umask(0o022)
    for key_id in certs_out:
        key_id_str = key_id.hex()
        log.info("Writing certificate with key ID {}".format(key_id_str))
        cert = certs_out[key_id]
        cert_pem = cert.public_bytes(primitives.serialization.Encoding.PEM)
        filename = "{}/{}.pem".format(destination_dir, key_id_str)
        with open(filename, 'wb') as binary_file:
            binary_file.write(cert_pem)

    os.umask(old_mask)
    log.info("Done saving certificates. Did {} of them.".format(len(certs_out)))

    return certs_out


def fetch_certificates_austria_api(destination_dir: str) -> dict:
    log.debug("Get trust list from Austria API endpoint: {}".format(API_ENDPOINT_AUSTRIA))
    response = requests.get(API_ENDPOINT_AUSTRIA, timeout=5.0)
    response.raise_for_status()

    json_data = response.json()
    epoc_utc_str = json_data['epochUTC']
    epoc_utc = datetime.utcfromtimestamp(epoc_utc_str // 1000)
    list_timestamp_str = json_data['trustList']['timeStamp']
    list_timestamp = datetime.strptime(list_timestamp_str, '%Y-%m-%dT%H:%M:%S.%f')
    signature_base64 = json_data['trustList']['trustListSignature']
    signature = base64.b64decode(signature_base64)
    list_base64 = json_data['trustList']['trustListContent']
    list_bytes = base64.b64decode(list_base64)

    if False:
        filename = "austria-cose.dat"
        with open(filename, "wb") as binary_file:
            binary_file.write(list_bytes)

        log.info("Wrote info into {}".format(filename))

    # Verify signature
    # Root certificate loaded from: https://github.com/Federal-Ministry-of-Health-AT/green-pass-overview/
    sig = CoseMessage.decode(signature)
    if not sig or not isinstance(sig, Sign1Message):
        raise RuntimeError("Not valid list!")

    at_root_cert_filename = "certs/roots/Austria-prod.pem"
    with open(at_root_cert_filename, "rb") as pem_file:
        lines = pem_file.read()
    root_cert = x509.load_pem_x509_certificate(lines)
    root_key = _cert_to_cose_key(root_cert)
    sig.key = root_key
    if not sig.verify_signature():
        raise RuntimeError("Austrian list doesn't verify!")
    log.info("Signature of {} verified ok.".format(API_ENDPOINT_AUSTRIA))

    # Save verified list of certificates
    return _save_certs(list_bytes, destination_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description='EU COVID Passport Signing Certificate Fetcher')
    parser.add_argument('--api-country', metavar="API-COUNTRY",
                        default=API_COUNTRY_AUSTRIA,
                        help='DGC API endpoint to use. Default: {0}, no authentication required there'.format(
                            API_COUNTRY_AUSTRIA))
    parser.add_argument('--cert-directory', default=DEFAULT_CERTS_DIR,
                        help="Destination directory to save certificates into. Default: {}".format(DEFAULT_CERTS_DIR))

    args = parser.parse_args()
    _setup_logger()

    certs = fetch_certificates(args.api_country, args.cert_directory)


if __name__ == '__main__':
    main()
