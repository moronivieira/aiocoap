import os, os.path
import tempfile
import json
from binascii import hexlify, unhexlify

from aiocoap import oscoap

contextdir = os.path.dirname(__file__) + '/common-context/'

def get_security_context(testno, role):
    os.makedirs('temp-contexts', exist_ok=True)
    contextcopy = tempfile.mkdtemp(prefix='context-', dir='temp-contexts')
    secretdata = json.load(open(contextdir + 'secret.json'))
    with open(os.path.join(contextcopy, 'secret.json'), 'w') as out:
        json.dump(secretdata, out)
    settingsdata = json.load(open(contextdir + 'settings.json'))

    # this needs to be messed with early, as key properties are derived
    # from this data
    if role == 'client':
        if testno == 10:
            settingsdata['client-sender-id_hex'] += '0000'

    with open(os.path.join(contextcopy, 'settings.json'), 'w') as out:
        json.dump(settingsdata, out)

    sequence = {
            "used": {(settingsdata['server-sender-id_hex'] if role == 'server' else settingsdata['client-sender-id_hex']).lower(): testno},
            "seen": {(settingsdata['client-sender-id_hex'] if role == 'server' else settingsdata['server-sender-id_hex']).lower(): list([testno - 1]) if role == 'server' else [-1]}
        }

    if role == 'client':
        if testno == 15:
            sequence["seen"][list(sequence["seen"].keys())[0]] = [65];

    with open(os.path.join(contextcopy, 'sequence.json'), 'w') as out:
        json.dump(sequence, out)

    print("Temporary context with seqno %d copied to %s"%(testno, contextcopy))
    secctx = oscoap.FilesystemSecurityContext(contextcopy, role=role)

    # this needs to be messed with late, as it is not explicit in the context
    # files
    if role == 'client':
        if testno == 11:
            secctx.sender_key = bytes(((secctx.sender_key[0] + 1)%256,)) + secctx.sender_key[1:]
        if testno == 12:
            secctx.recipient_key = bytes(((secctx.recipient_key[0] + 1)%256,)) + secctx.recipient_key[1:]

    original_extract_external_aad = secctx._extract_external_aad
    def _extract_extenal_aad(message, i_am_sender, request_partiv=None):
        result = original_extract_external_aad(message, i_am_sender, request_partiv)
        print("Verify: External AAD: %s"%(result,))
        return result
    secctx._extract_external_aad = _extract_extenal_aad

    return secctx

def additional_verify(description, lhs, rhs):
    if lhs == rhs:
        print("Additional verify passed: %s"%description)
    else:
        print("Additional verify failed (%s != %s): %s"%(lhs, rhs, description))
