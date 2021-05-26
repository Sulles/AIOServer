"""
Created: July 20, 2020
Updated: September 14, 2020
Author: Suleyman Barthe-Sukhera
Description: AES key class
TODO: Implement AESKey history to back-track incase encryption/transmission error and need to revert to prev key
"""

from typing import Union

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


"""
        # Break plain_text_message into 200 byte chunks because of GCM AES limit
        for start_byte in range(0, len(plain_text_message), 200):
            end_byte = start_byte + 200 if end_byte < len(plain_text_message) \
                else len(plain_text_message)

            plain_text_chunk =
"""

class AESKey:
    """ AES symmetric key object that can en/de/crypt messages """

    def __init__(self, name: str, common_logger: CommonLogger = None, **kwargs) -> None:
        """
        Initializer for AESKey object
        :param name: String name that this object will log itself with
        :param common_logger: CommonLogger object that this object will log with
        :param kwargs: Optional key word arguments to pass:
            - key: Bytes key for AES key to initialize with
            - nonce: Bytes nonce for AES key to initialize with
        """
        # General
        self.name = name
        self._logger = common_logger
        self.__key_len = 16

        # Current aes data
        self.__current_key = kwargs.pop('key', get_random_bytes(self.__key_len))
        self.__current_nonce = kwargs.pop('nonce', None)
        self.__current_aes = None

        # Next aes data
        self.__next_key = None
        self.__next_aes = None
        self.__next_nonce = None

        # AES step counter
        if 'server' in name.lower() or 'nexus' in name.lower():
            # Force servers and nexus connections to create new AES keys more frequently
            self.__max_key_usage = 10
        else:
            self.__max_key_usage = 20
        self.__key_usage_counter = 0

        # Build current and next key
        self.__build_current_aes()
        self.__build_next_aes()

    def __build_current_aes(self) -> None:
        """ Builds __current_aes using __current_key and __current_nonce """
        # Build current AES key
        self.__current_aes = AES.new(self.__current_key, AES.MODE_GCM, nonce=self.__current_nonce)

        # Update nonce from current AES (in case __current_nonce was None)
        self.__current_nonce = self.__current_aes.nonce

        # Set default next key to current key
        self.__next_key = self.__current_key
        self.debug('Built current AES')

    def __build_next_aes(self) -> None:
        """ Builds __next_aes using __next_key and __next_nonce """
        # Build next AES key
        self.__next_aes = AES.new(self.__next_key, AES.MODE_GCM, nonce=self.__next_nonce)

        # Update nonce (in case __next_nonce was None)
        self.__next_nonce = self.__next_aes.nonce
        self.debug('Built next AES')

    def __step_to_next_aes(self) -> None:
        """
        This method sets all self.__current values to all self.__next values,
        and creates new self.__next values
        """
        self.debug('Stepping to next AES keys...')
        # Track number of times using the same aes key
        if self.__current_key == self.__next_key:
            self.__key_usage_counter += 1
        else:  # reset on different key used
            self.__key_usage_counter = 0

        # Set __current values to __next values
        self.__current_key = self.__next_key
        self.__current_nonce = self.__next_nonce

        # Build new current aes
        self.__build_current_aes()
        self.__next_nonce = None  # Always default to None (will generate new nonce)
        self.__build_next_aes()

    def get_current_aes_details(self) -> dict:
        self.log('WARNING: Accessing current AES details!')
        return dict(key=self.__current_key, nonce=self.__current_nonce)

    def __update_next_aes_from_proto(self, next_key: AESKey_proto) -> None:
        """
        This method will take a AESKey_proto object
        and update self.__next values to match those provided
        """
        # Not all AESKey_proto messages will pass keys, check for it
        if next_key.aes_key:
            self.debug('Got new AES key')
            self.__next_key = next_key.aes_key

        # Always expect a nonce
        self.__next_nonce = next_key.aes_nonce

    def __build_aes_encrypted_payload(self, **kwargs) -> Union[bytes, None]:
        # Build AESEncryptedPayload
        aes_encrypted_payload = AESEncryptedPayload_proto()

        # Insert message
        for field, value in kwargs.items():
            if field not in aes_encrypted_payload.DESCRIPTOR.fields_by_name.keys():
                self.log(f'"{field}" was not a known field of {aes_encrypted_payload.DESCRIPTOR.name}, '
                         f'expected: {aes_encrypted_payload.DESCRIPTOR.fields_by_name.keys()}')
                return None
            setattr(aes_encrypted_payload, field, value)

        # Check key usage, set different next key if key usage counter exceeds max usages
        if self.__key_usage_counter >= self.__max_key_usage:
            self.debug(f'Key counter reached max usage: {self.__max_key_usage}, creating new key')
            self.__next_key = get_random_bytes(self.__key_len)

        # Build next AES key if different than current one
        if self.__next_key != self.__current_key:
            aes_encrypted_payload.next_aes_key.aes_key = self.__next_key

        # Build next nonce
        aes_encrypted_payload.next_aes_key.aes_nonce = self.__next_nonce
        self.debug(f'Built AESEncryptedPayload with message: {aes_encrypted_payload}')
        return aes_encrypted_payload.SerializeToString()

    def encrypt(self, **kwargs) -> bytes:
        """ Takes plaintext or other protobuf message object and returns AESSecureMessage """
        # Build AESSecureMessage
        aes_secure_msg = AESSecureMessage_proto()
        try:
            # Build AESEncryptedPayload
            aes_encrypted_payload = self.__build_aes_encrypted_payload(**kwargs)

            # Encrypt AESEncryptedPayload and add to AESSecureMessage
            ciphertext, tag = self.__current_aes.encrypt_and_digest(aes_encrypted_payload)
            self.debug(f'ciphertext: {ciphertext}')
            self.debug(f'tag: {tag}')

        except Exception as e:
            self.log(f'CRITICAL ERROR 0: Failed to encrypt message with error: {e}')
            raise e

        # Flush out all attributes of AESSecureMessage
        aes_secure_msg.aes_encrypted_payload = ciphertext
        aes_secure_msg.tag = tag

        # AES has been used, step to next one
        self.__step_to_next_aes()
        self.debug(f'Built secure message:\n{aes_secure_msg}')
        return aes_secure_msg.SerializeToString()

    def decrypt(self, message: bytes) -> bytes:
        """
        Takes bytestream of AESSecureMessage and decrypts AESEncryptedPayload,
        returns bytes message
        """
        # Build AESSecureMessage
        self.debug(f'Starting decryption of: {message}')
        aes_secure_msg = AESSecureMessage_proto()
        aes_secure_msg.ParseFromString(message)

        # Build AESEncryptedPayload
        decrypted_payload = AESEncryptedPayload_proto()
        try:
            decrypted_payload.ParseFromString(
                self.__current_aes.decrypt_and_verify(
                    aes_secure_msg.aes_encrypted_payload, aes_secure_msg.tag))
            self.debug(f'Decrypted AES message: {decrypted_payload}')

        except Exception as e:
            self.log(f'CRITICAL ERROR 1: '
                     f'Failed to decrypt and authenticate message with error:\n{e}')
            raise e

        self.__update_next_aes_from_proto(decrypted_payload.next_aes_key)
        self.__step_to_next_aes()  # Used current aes to decrypt, need to step to next aes
        return decrypted_payload

    """ === MISC === """

    def log(self, log) -> None:
        if self._logger is not None:
            self._logger.log(f'[{self.name}] {log}')
        else:
            print(f'[{self.name}] {log}')

    def debug(self, log) -> None:
        if self._logger is not None:
            self._logger.debug(f'[{self.name}] {log}')
