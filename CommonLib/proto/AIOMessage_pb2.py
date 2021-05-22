# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: AIOMessage.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import Base_pb2 as Base__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='AIOMessage.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x10\x41IOMessage.proto\x1a\nBase.proto\"\xdc\x01\n\nAIOMessage\x12(\n\x0f\x65ncryption_type\x18\x01 \x01(\x0e\x32\x0f.EncryptionType\x12\x1c\n\x14\x65ncryption_timestamp\x18\x02 \x01(\x02\x12\x14\n\x0cmessage_name\x18\x03 \x01(\t\x12\x0f\n\x07message\x18\x04 \x01(\x0c\x12\x19\n\x11\x65ncrypted_message\x18\x05 \x03(\x0c\x12\x0b\n\x03tag\x18\x06 \x03(\x0c\x12\x15\n\x05\x65rror\x18\x07 \x01(\x0b\x32\x06.Error\x12 \n\x0b\x63lient_info\x18\x08 \x01(\x0b\x32\x0b.ClientInfob\x06proto3'
  ,
  dependencies=[Base__pb2.DESCRIPTOR,])




_AIOMESSAGE = _descriptor.Descriptor(
  name='AIOMessage',
  full_name='AIOMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='encryption_type', full_name='AIOMessage.encryption_type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='encryption_timestamp', full_name='AIOMessage.encryption_timestamp', index=1,
      number=2, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message_name', full_name='AIOMessage.message_name', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message', full_name='AIOMessage.message', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=b"",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='encrypted_message', full_name='AIOMessage.encrypted_message', index=4,
      number=5, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tag', full_name='AIOMessage.tag', index=5,
      number=6, type=12, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='error', full_name='AIOMessage.error', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='client_info', full_name='AIOMessage.client_info', index=7,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=33,
  serialized_end=253,
)

_AIOMESSAGE.fields_by_name['encryption_type'].enum_type = Base__pb2._ENCRYPTIONTYPE
_AIOMESSAGE.fields_by_name['error'].message_type = Base__pb2._ERROR
_AIOMESSAGE.fields_by_name['client_info'].message_type = Base__pb2._CLIENTINFO
DESCRIPTOR.message_types_by_name['AIOMessage'] = _AIOMESSAGE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

AIOMessage = _reflection.GeneratedProtocolMessageType('AIOMessage', (_message.Message,), {
  'DESCRIPTOR' : _AIOMESSAGE,
  '__module__' : 'AIOMessage_pb2'
  # @@protoc_insertion_point(class_scope:AIOMessage)
  })
_sym_db.RegisterMessage(AIOMessage)


# @@protoc_insertion_point(module_scope)
