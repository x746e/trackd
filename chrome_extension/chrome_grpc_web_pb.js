/**
 * @fileoverview gRPC-Web generated client stub for trackd
 * @enhanceable
 * @public
 */

// GENERATED CODE -- DO NOT EDIT!


/* eslint-disable */
// @ts-nocheck



const grpc = {};
grpc.web = require('grpc-web');


var google_protobuf_empty_pb = require('google-protobuf/google/protobuf/empty_pb.js')
const proto = {};
proto.trackd = require('./chrome_pb.js');

/**
 * @param {string} hostname
 * @param {?Object} credentials
 * @param {?Object} options
 * @constructor
 * @struct
 * @final
 */
proto.trackd.ChromeClient =
    function(hostname, credentials, options) {
  if (!options) options = {};
  options['format'] = 'binary';

  /**
   * @private @const {!grpc.web.GrpcWebClientBase} The client
   */
  this.client_ = new grpc.web.GrpcWebClientBase(options);

  /**
   * @private @const {string} The hostname
   */
  this.hostname_ = hostname;

};


/**
 * @param {string} hostname
 * @param {?Object} credentials
 * @param {?Object} options
 * @constructor
 * @struct
 * @final
 */
proto.trackd.ChromePromiseClient =
    function(hostname, credentials, options) {
  if (!options) options = {};
  options['format'] = 'binary';

  /**
   * @private @const {!grpc.web.GrpcWebClientBase} The client
   */
  this.client_ = new grpc.web.GrpcWebClientBase(options);

  /**
   * @private @const {string} The hostname
   */
  this.hostname_ = hostname;

};


/**
 * @const
 * @type {!grpc.web.MethodDescriptor<
 *   !proto.trackd.SessionChangedRequest,
 *   !proto.google.protobuf.Empty>}
 */
const methodDescriptor_Chrome_session_changed = new grpc.web.MethodDescriptor(
  '/trackd.Chrome/session_changed',
  grpc.web.MethodType.UNARY,
  proto.trackd.SessionChangedRequest,
  google_protobuf_empty_pb.Empty,
  /**
   * @param {!proto.trackd.SessionChangedRequest} request
   * @return {!Uint8Array}
   */
  function(request) {
    return request.serializeBinary();
  },
  google_protobuf_empty_pb.Empty.deserializeBinary
);


/**
 * @const
 * @type {!grpc.web.AbstractClientBase.MethodInfo<
 *   !proto.trackd.SessionChangedRequest,
 *   !proto.google.protobuf.Empty>}
 */
const methodInfo_Chrome_session_changed = new grpc.web.AbstractClientBase.MethodInfo(
  google_protobuf_empty_pb.Empty,
  /**
   * @param {!proto.trackd.SessionChangedRequest} request
   * @return {!Uint8Array}
   */
  function(request) {
    return request.serializeBinary();
  },
  google_protobuf_empty_pb.Empty.deserializeBinary
);


/**
 * @param {!proto.trackd.SessionChangedRequest} request The
 *     request proto
 * @param {?Object<string, string>} metadata User defined
 *     call metadata
 * @param {function(?grpc.web.Error, ?proto.google.protobuf.Empty)}
 *     callback The callback function(error, response)
 * @return {!grpc.web.ClientReadableStream<!proto.google.protobuf.Empty>|undefined}
 *     The XHR Node Readable Stream
 */
proto.trackd.ChromeClient.prototype.session_changed =
    function(request, metadata, callback) {
  return this.client_.rpcCall(this.hostname_ +
      '/trackd.Chrome/session_changed',
      request,
      metadata || {},
      methodDescriptor_Chrome_session_changed,
      callback);
};


/**
 * @param {!proto.trackd.SessionChangedRequest} request The
 *     request proto
 * @param {?Object<string, string>} metadata User defined
 *     call metadata
 * @return {!Promise<!proto.google.protobuf.Empty>}
 *     Promise that resolves to the response
 */
proto.trackd.ChromePromiseClient.prototype.session_changed =
    function(request, metadata) {
  return this.client_.unaryCall(this.hostname_ +
      '/trackd.Chrome/session_changed',
      request,
      metadata || {},
      methodDescriptor_Chrome_session_changed);
};


module.exports = proto.trackd;

