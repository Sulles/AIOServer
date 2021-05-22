"""
Authenticator service

All new connections to AIOServer must go through the following steps:

1. Client -> Server: AIOMessage(
        encryption_type = RSA,
        encryption_timestamp = timestamp default Server RSA key was created,
        message_name = "Authenticator",
        message = {AuthenticationStep = NEW_SESSION,
                   new_rsa_key = RSAKey(client public RSA key)
                  }
        )
2. Server -> Client: AIOMessage(
        encryption_type = RSA,
        encryption_timestamp = timestamp that client provided from (1.new_rsa_key),
        message_name = "Authenticator",
        message =  {AuthenticationStep = NEW_RSA,
                    new_rsa_key = RSAKey(server non-default Server public RSA key)
                   }
        )
3. Client -> Server: AIOMessage(
        encryption_type = RSA,
        encryption_timestamp = timestamp that server provided from (2.new_rsa_key),
        message_name = "Authenticator",
        message = {AuthenticationStep = CONFIRMATION}
        )
4. Server -> Client: AIOMessage(
        encryption_type = RSA,
        encryption_timestamp = timestamp that client provided from (1.new_rsa_key)
        message_name = "Authenticator",
        message = {AuthenticationStep = NEW_AES,
                   new_aes_key = AESKey(server initiated AES GCM key)
                   }
        )
5. Client -> Server: AIOMessage(
        encryption_type = AES,
        encryption_timestamp = timestamp that server provided from (4.new_aes_key),
        message_name = "Authenticator",
        message = {AuthenticationStep = CONFIRMATION}
        )
"""

import trio.lowlevel

from CommonLib.proto.Authenticator_pb2 import AuthenticatorMessage


class Authenticator:
    def __init__(self, register_service: classmethod):
        """
        Register all message -> handler relations to service registerer callback
        """
        pass

    def _handle_authenticator_message(self, message: bytes,
                                      response_callback: trio.lowlevel.wait_writable):
        """ Callback for every client Authenticator message """
        auth_message = AuthenticatorMessage()
        auth_message.ParseFromString(message)
        # TODO: Finish this...
        raise NotImplementedError
