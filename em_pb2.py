# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: em.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'em.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x08\x65m.proto\x12\x11\x65xclusion_manager\"L\n\x0eRequestMessage\x12\x11\n\ttimestamp\x18\x01 \x01(\x03\x12\x12\n\nprocess_id\x18\x02 \x01(\t\x12\x13\n\x0bresource_id\x18\x03 \x01(\t\"W\n\x0cReplyMessage\x12\x11\n\ttimestamp\x18\x01 \x01(\x03\x12\x12\n\nprocess_id\x18\x02 \x01(\t\x12\x0f\n\x07granted\x18\x03 \x01(\x08\x12\x0f\n\x07message\x18\x04 \x01(\t\"L\n\x0eReleaseMessage\x12\x11\n\ttimestamp\x18\x01 \x01(\x03\x12\x12\n\nprocess_id\x18\x02 \x01(\t\x12\x13\n\x0bresource_id\x18\x03 \x01(\t\"#\n\rStatusRequest\x12\x12\n\nprocess_id\x18\x01 \x01(\t\"v\n\x0eStatusResponse\x12\x12\n\nprocess_id\x18\x01 \x01(\t\x12\x1b\n\x13in_critical_section\x18\x02 \x01(\x08\x12\x19\n\x11\x63urrent_timestamp\x18\x03 \x01(\x03\x12\x18\n\x10pending_requests\x18\x04 \x03(\t2\xde\x02\n\x10\x45xclusionManager\x12R\n\x0cRequestEntry\x12!.exclusion_manager.RequestMessage\x1a\x1f.exclusion_manager.ReplyMessage\x12P\n\nReplyEntry\x12!.exclusion_manager.RequestMessage\x1a\x1f.exclusion_manager.ReplyMessage\x12R\n\x0cReleaseEntry\x12!.exclusion_manager.ReleaseMessage\x1a\x1f.exclusion_manager.ReplyMessage\x12P\n\tGetStatus\x12 .exclusion_manager.StatusRequest\x1a!.exclusion_manager.StatusResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'em_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_REQUESTMESSAGE']._serialized_start=31
  _globals['_REQUESTMESSAGE']._serialized_end=107
  _globals['_REPLYMESSAGE']._serialized_start=109
  _globals['_REPLYMESSAGE']._serialized_end=196
  _globals['_RELEASEMESSAGE']._serialized_start=198
  _globals['_RELEASEMESSAGE']._serialized_end=274
  _globals['_STATUSREQUEST']._serialized_start=276
  _globals['_STATUSREQUEST']._serialized_end=311
  _globals['_STATUSRESPONSE']._serialized_start=313
  _globals['_STATUSRESPONSE']._serialized_end=431
  _globals['_EXCLUSIONMANAGER']._serialized_start=434
  _globals['_EXCLUSIONMANAGER']._serialized_end=784
# @@protoc_insertion_point(module_scope)
