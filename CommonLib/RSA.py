"""
Created: March 1, 2020
Updated: September 14, 2020
Author: Suleyman Barthe-Sukhera
Description: RSA private and public key classes
"""

from binascii import hexlify, unhexlify
from os import getcwd

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash.SHA3_256 import SHA3_256_Hash
from Crypto.PublicKey.RSA import \
    generate as generate_rsa_key, \
    import_key as import_rsa_key, \
    construct as construct_rsa_key, \
    RsaKey as CryptoRSAKey

from CommonLib.proto.AIOMessage_pb2 import AIOMessage
from CommonLib.proto.Base_pb2 import EncryptionType, Error, ErrorCode


class BaseRSAKey:
    def __init__(self, name: str, rsa_key: CryptoRSAKey):
        self.name = name
        self.__rsa_key = rsa_key
        self.__cipher = self.__cipher = PKCS1_OAEP.new(rsa_key, hashAlgo=SHA3_256_Hash)

    """ === ENCRYPTION === """

    def encrypt(self, message: AIOMessage) -> AIOMessage:
        """ Encrypts AIOMessage.message contents """
        # Set encryption type to RSA
        message.encryption_type = EncryptionType.RSA

        # Grab plain_text_message, and remove plain_text_message from message
        plain_text_message = message.message
        message.ClearField('message')

        # Encrypt plain_text_message and insert as encrypted message
        try:
            message.encrypted_messages.Extend([self.__cipher.encrypt(plain_text_message)])
        except Exception as e:
            error = Error()
            error.error_code = ErrorCode.ENCRYPTION_ERR0R
            error.error_details = str(e)
            print(f'WARNING - ENCRYPTION FAILURE: {e}')
            message.error.ParseFromString(error.SerializeToString())

        # TODO: Add encryption timestamp
        return message

    """ === DECRYPTION === """

    def decrypt(self, message: AIOMessage) -> AIOMessage:
        """ Decrypts AIOMessage.encrypted_message contents """
        # Make sure encryption type is correct
        assert message.encryption_type == EncryptionType.RSA, \
            f'Expected RSA encryption, got: {message.encryption_type}!'

        # Make sure there is only one message for RSA encrypted messages
        encrypted_messages = [encrypted_message for encrypted_message in message.encrypted_messages]
        assert len(encrypted_messages) == 1, \
            f'RSA encryption only expects one encrypted message, ' \
            f'received {len(encrypted_messages)} encrypted messages!'

        # Populate plain text message field and remove encrypted message and encrypted message type
        try:
            message.message = self.__cipher.decrypt(encrypted_messages[0])
            message.ClearField('encrypted_messages')
            message.ClearField('encryption_type')
        except Exception as e:
            error = Error()
            error.error_code = ErrorCode.DECRYPTION_ERROR
            error.error_details = str(e)
            print(f'WARNING - DECRYPTION FAILURE: {e}')
            message.error.ParseFromString(error.SerializeToString())

        # Return decrypted message
        return message

    """ === GETTERS === """

    def get_pub_key_details(self):
        return self.__rsa_key.n, self.__rsa_key.e


class PrivateRSAKey(BaseRSAKey):
    """ Private RSA asymmetric key that can en/de/crypt messages """

    def __init__(
            self, name: str, rsa_pwd: str, mod_len: int = 2048,
            rsa_key_path: str = f'{getcwd()}\\User\\Keys\\rsa.pem') -> None:
        """
        Base initializer for RSAKey, will try and load an existing RSAKey before creating a new one
        :param name: String name that this object will log itself with
        :param rsa_pwd: Bytes used to decode rsa.pem
        :param mod_len: Modulus length for creating RSA key, default to 2048
        :param rsa_key_path: Optional modifier of default path to RSA key
        """
        self.name = name
        self.__modulus_len = mod_len
        self.rsa_key_path = rsa_key_path

        try:
            print('Loading existing RSA keys...')
            with open(self.rsa_key_path, 'r') as rsa_file:
                imported_key = rsa_file.read().encode('utf-8')
                imported_key = unhexlify(imported_key)
                __private_rsa_key = import_rsa_key(imported_key, passphrase=rsa_pwd)

        except (FileNotFoundError, ValueError) as e:
            if type(e) is ValueError:
                print('Failed to parse existing RSA keys, creating new ones...')
            elif type(e) is FileNotFoundError:
                print('RSA keys do not exist, creating new ones...')
            __private_rsa_key = generate_rsa_key(mod_len, e=23981519)
            with open(self.rsa_key_path, 'w+') as rsa_file:
                exportable_key = hexlify(__private_rsa_key.export_key(
                    format='DER', passphrase=rsa_pwd, pkcs=8))
                rsa_file.write(exportable_key.decode('utf-8'))
            print('RSA keys created and saved!')

        except Exception as e:
            print(f'CRITICAL ERROR 0: Failed to initialize RSA keys with error:\n{e}')
            raise e

        # Build rest of RSA key functionality
        BaseRSAKey.__init__(self, name, __private_rsa_key)
        print('Successfully initialized PrivateRSAKey')

    """ === GETTERS === """

    def get_public_key(self) -> dict:
        """ returns 'n' and 'e' """
        pub_key_details = self.get_pub_key_details()
        return dict(
            n=pub_key_details[0].to_bytes(length=int(self.__modulus_len / 8), byteorder='big'),
            e=pub_key_details[1].to_bytes(length=4, byteorder='big'))


class PublicRSAKey(BaseRSAKey):
    def __init__(self, name: str, pub_key_details: dict) -> None:
        self.name = name

        # Build rest of RSA key functionality
        BaseRSAKey.__init__(
            self, name, construct_rsa_key(
                (int.from_bytes(pub_key_details['n'], byteorder='big'),
                 int.from_bytes(pub_key_details['e'], byteorder='big'))))
        print('Successfully initialized PublicRSAKey')
